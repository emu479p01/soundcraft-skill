"""Opt-in fallback installer for Python 3.9+, using only the standard library.

Inspect with --dry-run before applying. Existing different skills/servers are
conflicts: move or reconcile them explicitly, then rerun. No paths are deleted.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
from datetime import datetime
import json
import os
from pathlib import Path
import re
import secrets
import shutil
import stat
import sys


MCP_SERVER = {"command": "soundcraft-cli", "args": ["mcp"]}
_KEY = re.compile(r'''[A-Za-z0-9_-]+|"(?:\\.|[^"\\])*"|'[^']*' ''', re.VERBOSE)


def _conflict(path: Path, component: str) -> ValueError:
    return ValueError(
        f"Conflict at {path}: {component}; move, rename, or resolve the existing "
        "entry manually, then rerun (nothing is overwritten)."
    )


def _keys(text: str, path: Path) -> tuple[str, ...]:
    """Read simple TOML key paths; refuse syntax this append-only editor cannot prove safe."""
    result = []
    remaining = text.strip()
    while remaining:
        match = _KEY.match(remaining)
        if not match:
            raise _conflict(path, 'soundcraft configuration uses unsupported TOML key syntax')
        token = match.group()
        try:
            result.append(json.loads(token) if token.startswith('"') else token.strip("'"))
        except ValueError:
            raise _conflict(path, 'soundcraft configuration uses unsupported TOML escapes') from None
        remaining = remaining[match.end():].strip()
        if not remaining:
            break
        if not remaining.startswith('.'):
            raise _conflict(path, 'soundcraft configuration uses unsupported TOML key syntax')
        remaining = remaining[1:].strip()
        if not remaining:
            raise _conflict(path, 'soundcraft configuration has an incomplete TOML key')
    return tuple(result)


def _codex_content(original: bytes, path: Path) -> bytes:
    """Append only; never reinterpret or rewrite the caller's unrelated TOML."""
    text = original.decode('utf-8-sig')
    # Triple-quote markers require lexical state this small editor cannot prove
    # safe. Refuse conservatively, even inside comments or single-line strings.
    if '"""' in text or "'''" in text:
        raise _conflict(path, 'unsupported multiline TOML; configure soundcraft manually')
    section = ()
    server_sections = []
    server_values = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith('#'):
            continue
        header = re.fullmatch(r'\[([^\[\]]+)\]\s*(?:#.*)?', stripped)
        if header:
            section = _keys(header.group(1), path)
            if section[:2] == ('mcp_servers', 'soundcraft'):
                server_sections.append(section)
            continue
        # An array of tables, multiline key, or other ambiguous MCP syntax is
        # deliberately a conflict rather than risking a duplicate declaration.
        if stripped.startswith('['):
            if 'mcp_servers' in stripped or section[:2] == ('mcp_servers', 'soundcraft'):
                raise _conflict(path, 'soundcraft configuration uses an ambiguous TOML table')
            section = ('__unsupported_table__',)
            continue
        assignment = re.match(r'([^=]+)=(.*)', stripped)
        if assignment:
            key_text, value = assignment.groups()
            # Unrecognized MCP keys must not hide an existing server.
            try:
                key = _keys(key_text, path)
            except ValueError:
                if section[:1] == ('mcp_servers',) or 'mcp_servers' in key_text:
                    raise
                continue
            full_key = section + key
            if full_key == ('mcp_servers',) or full_key[:2] == ('mcp_servers', 'soundcraft'):
                if section == ('mcp_servers', 'soundcraft') and key in (('command',), ('args',)):
                    server_values.append((key[0], value.strip()))
                else:
                    raise _conflict(path, 'soundcraft server is already defined differently')
        elif section[:2] == ('mcp_servers', 'soundcraft'):
            raise _conflict(path, 'soundcraft server has an unsupported multiline value')
    if server_sections:
        expected = {'command': json.dumps(MCP_SERVER['command']), 'args': json.dumps(MCP_SERVER['args'])}
        if (server_sections == [('mcp_servers', 'soundcraft')]
                and len(server_values) == len(expected) and dict(server_values) == expected):
            return original
        raise _conflict(path, 'soundcraft server is already defined differently')
    newline = '\r\n' if b'\r\n' in original else '\n'
    block = newline.join([
        '[mcp_servers.soundcraft]',
        'command = ' + json.dumps(MCP_SERVER['command']),
        'args = ' + json.dumps(MCP_SERVER['args']), '',
    ]).encode('utf-8')
    separator = (b'' if not original else newline.encode('ascii') * (1 if original.endswith(b'\n') else 2))
    return original + separator + block


def _antigravity_content(original: bytes, path: Path) -> bytes:
    def unique_object(pairs):
        data = {}
        for key, value in pairs:
            if key in data:
                raise ValueError(f'duplicate key {key!r}; resolve it manually before installing')
            data[key] = value
        return data

    try:
        data = json.loads(original.decode('utf-8-sig'), object_pairs_hook=unique_object) if original else {}
    except (ValueError, UnicodeError) as exc:
        raise ValueError(f"Invalid JSON at {path}: {exc}") from None
    if not isinstance(data, dict) or not isinstance(data.get('mcpServers', {}), dict):
        raise ValueError(f"Invalid JSON at {path}: expected an object with an mcpServers object")
    servers = data.setdefault('mcpServers', {})
    if 'soundcraft' in servers:
        if servers['soundcraft'] == MCP_SERVER:
            return original
        raise _conflict(path, 'soundcraft server is already defined differently')
    servers['soundcraft'] = MCP_SERVER
    return (json.dumps(data, ensure_ascii=False, indent=2) + '\n').encode('utf-8')


def _safe_parent(path: Path, home: Path) -> None:
    """Reject redirected parent directories, including Windows junctions."""
    for parent in (path.parent, *path.parent.parents):
        if parent == home:
            break
        if home not in parent.parents:
            raise _conflict(path, 'destination is outside the supplied home')
        if parent.is_symlink() or parent.resolve() != parent:
            raise _conflict(path, 'destination parent is a symlink or redirected directory')


def _tree(path: Path) -> dict:
    """Compare complete contents without following links or removing caller files."""
    result = {}
    if path.is_symlink() or path.resolve() != path or not path.is_dir():
        raise _conflict(path, 'skill directory is a link or is not a directory')
    for child in sorted(path.rglob('*')):
        if child.is_symlink() or child.resolve() != child:
            raise _conflict(child, 'skill contains a symlink or redirected directory')
        if not child.is_file() and not child.is_dir():
            raise _conflict(child, 'skill contains a non-regular entry')
        result[child.relative_to(path)] = child.read_bytes() if child.is_file() else None
    return result


def _backup_stamp() -> str:
    return datetime.now().strftime('%Y%m%d%H%M%S')


def _backup(path: Path, original: bytes) -> Path:
    """Exclusive creation prevents overwriting backups even within one second."""
    base = path.with_name(path.name + '.bak-' + _backup_stamp())
    candidate = base
    suffix = 0
    while True:
        try:
            with candidate.open('xb') as stream:
                stream.write(original)
            return candidate
        except FileExistsError:
            suffix += 1
            candidate = base.with_name(base.name + '-' + str(suffix))


def _config_identity(path: Path):
    try:
        info = path.lstat()
    except FileNotFoundError:
        return None
    if not stat.S_ISREG(info.st_mode):
        raise _conflict(path, 'soundcraft config is not a regular file')
    return (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns)


def _check_config(path: Path, home: Path, identity, original: bytes) -> None:
    _safe_parent(path, home)
    if _config_identity(path) != identity:
        raise _conflict(path, 'soundcraft config changed during installation')
    if identity is not None:
        # O_NOFOLLOW closes the stat/open link race on platforms providing it.
        descriptor = os.open(path, os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0))
        with os.fdopen(descriptor, 'rb') as stream:
            if stream.read() != original:
                raise _conflict(path, 'soundcraft config changed during installation')


@contextmanager
def _config_directory(path: Path, home: Path):
    """Anchor sibling creation/replacement against concurrent parent redirection."""
    _safe_parent(path, home)
    if os.name == 'nt':
        import ctypes
        from ctypes import wintypes

        kernel = ctypes.WinDLL('kernel32', use_last_error=True)
        create = kernel.CreateFileW
        create.argtypes = (wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD,
                           wintypes.LPVOID, wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE)
        create.restype = wintypes.HANDLE
        close = kernel.CloseHandle
        close.argtypes = (wintypes.HANDLE,)
        close.restype = wintypes.BOOL
        handles = []
        try:
            # Deny directory deletion/rename while allowing child file updates.
            parents = [path.parent, *path.parent.parents]
            for parent in reversed(parents[:parents.index(home) + 1]):
                handle = create(str(parent), 0x80000000, 3, None, 3, 0x02200000, None)
                # GENERIC_READ, OPEN_EXISTING, BACKUP_SEMANTICS | OPEN_REPARSE_POINT.
                if handle == wintypes.HANDLE(-1).value:
                    raise ctypes.WinError(ctypes.get_last_error())
                handles.append(handle)
            _safe_parent(path, home)
            yield None
        finally:
            for handle in reversed(handles):
                close(handle)
    else:
        descriptor = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        try:
            _safe_parent(path, home)
            if not os.path.samestat(os.fstat(descriptor), path.parent.stat()):
                raise _conflict(path, 'destination parent changed during installation')
            yield descriptor
        finally:
            os.close(descriptor)


def _replace_config(path: Path, home: Path, identity, original: bytes, updated: bytes) -> None:
    _check_config(path, home, identity, original)
    with _config_directory(path, home) as directory:
        _check_config(path, home, identity, original)
        name = '.' + path.name + '.tmp-' + secrets.token_hex(16)
        temporary = path.with_name(name)
        location = temporary if directory is None else name
        options = {} if directory is None else {'dir_fd': directory}
        descriptor = os.open(location, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600, **options)
        try:
            with os.fdopen(descriptor, 'wb') as stream:
                stream.write(updated)
                stream.flush()
                os.fsync(stream.fileno())
            _check_config(path, home, identity, original)
            if directory is None:
                os.replace(temporary, path)
            else:
                os.replace(name, path.name, src_dir_fd=directory, dst_dir_fd=directory)
        finally:
            try:
                os.unlink(location, **options)
            except FileNotFoundError:
                pass


def install(targets: list[str], home: Path, repo: Path, dry_run: bool = False,
            link: bool = False) -> list[str]:
    """Plan all targets before writes; return actions. Conflicts raise ValueError.

    Copies and correct links are left untouched on repeat runs. Different
    destinations require manual reconciliation; this installer never deletes.
    """
    unknown = set(targets) - {'codex', 'antigravity'}
    if unknown:
        raise ValueError('Unknown install target(s): ' + ', '.join(sorted(unknown)))
    if not targets:
        return []
    home, repo = Path(home).resolve(), Path(repo).resolve()
    source = repo / 'skills'
    if not source.is_dir() or source.is_symlink() or source.resolve() != source:
        raise ValueError(f"Missing or redirected skills directory: {source}")
    skills = sorted(p for p in source.iterdir() if p.is_dir() or p.is_symlink())
    if not skills:
        raise ValueError(f"No skills directories in {source}")
    source_trees = {skill: _tree(skill) for skill in skills}
    configs, copies, actions = [], [], []
    prefix = 'Would ' if dry_run else ''
    for target in dict.fromkeys(targets):
        if target == 'codex':
            skill_root = home / '.agents/skills'
            config = home / '.codex/config.toml'
            merge = _codex_content
        else:
            skill_root = home / '.gemini/config/skills'
            config = home / '.gemini/config/mcp_config.json'
            merge = _antigravity_content
        _safe_parent(config, home)
        identity = _config_identity(config)
        original = config.read_bytes() if identity is not None else b''
        updated = merge(original, config)
        if updated != original:
            configs.append((config, identity, original, updated))
        else:
            actions.append(f"Unchanged config: {config}")
        for skill in skills:
            dest = skill_root / skill.name
            _safe_parent(dest, home)
            if dest.is_symlink():
                if dest.resolve() != skill:
                    raise _conflict(dest, f'skill {skill.name} links somewhere else')
                actions.append(f"Unchanged skill link: {dest}")
            elif dest.exists():
                if _tree(dest) != source_trees[skill]:
                    raise _conflict(dest, f'skill {skill.name} has different contents')
                actions.append(f"Unchanged skill: {dest}")
            else:
                copies.append((skill, dest))
    # No filesystem changes above this line, including on dry-run/conflict.
    for skill, dest in copies:
        verb = 'link' if link else 'copy'
        actions.append(f"{prefix}{verb} skill {skill} -> {dest}")
        if dry_run:
            continue
        dest.parent.mkdir(parents=True, exist_ok=True)
        if link:
            try:
                dest.symlink_to(skill, target_is_directory=True)
                continue
            except OSError as exc:
                # A concurrent or partially created destination must not be followed.
                if dest.exists() or dest.is_symlink():
                    raise _conflict(dest, f'skill {skill.name} appeared during symlink creation') from exc
                actions.append(f"Warning: symlink failed ({exc}); falling back to copy: {dest}")
        shutil.copytree(skill, dest)
    for config, identity, original, updated in configs:
        actions.append(f"{prefix}merge soundcraft MCP server into {config}")
        if dry_run:
            if config.exists():
                actions.append(f"Would back up {config} before editing")
            continue
        config.parent.mkdir(parents=True, exist_ok=True)
        _check_config(config, home, identity, original)
        if identity is not None:
            actions.append(f"Backup: {_backup(config, original)}")
        _replace_config(config, home, identity, original, updated)
    return actions


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--codex', action='store_true', help='Install skills and MCP for Codex')
    parser.add_argument('--antigravity', action='store_true', help='Install skills and MCP for Antigravity')
    parser.add_argument('--all', action='store_true', help='Install both fallback targets')
    parser.add_argument('--dry-run', action='store_true', help='Show actions without any writes')
    parser.add_argument('--link', action='store_true', help='Link skills; copy with a warning if unavailable')
    args = parser.parse_args(argv)
    repo = Path(__file__).resolve().parent
    targets = [name for name in ('codex', 'antigravity') if args.all or getattr(args, name)]
    if not targets:
        parser.print_help()
    print(f'Claude Code: /plugin marketplace add "{repo}"')
    print('Then: /plugin install soundcraft-skills@soundcraft-skills')
    if not targets:
        return 0
    try:
        for line in install(targets, Path.home(), repo, args.dry_run, args.link):
            print(line)
    except (OSError, ValueError) as exc:
        print(f'Install failed: {exc}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
