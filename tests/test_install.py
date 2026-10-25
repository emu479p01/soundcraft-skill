"""Fallback installation tests use fake repositories and homes exclusively."""
from contextlib import redirect_stdout
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch


SCRIPT = Path(__file__).resolve().parents[1] / 'install.py'


class InstallTests(unittest.TestCase):
    def setUp(self):
        self.assertTrue(SCRIPT.is_file(), 'The fallback installer is missing')
        spec = importlib.util.spec_from_file_location('soundcraft_installer', SCRIPT)
        self.installer = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.installer)
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.home = self.root / 'fake home'
        self.repo = self.root / 'fake repo'
        self.skill = self.repo / 'skills/chords'
        self.skill.mkdir(parents=True)
        (self.skill / 'SKILL.md').write_text('---\nname: chords\ndescription: Fake chords.\n---\n', encoding='utf-8')
        self.toml = self.home / '.codex/config.toml'
        self.json = self.home / '.gemini/config/mcp_config.json'

    def write(self, path, content):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content.encode('utf-8'))

    def snapshot(self):
        return {str(p.relative_to(self.home)): (p.read_bytes() if p.is_file() else None)
                for p in self.home.rglob('*')} if self.home.exists() else {}

    def run_install(self, targets=None, **kwargs):
        return self.installer.install(targets or ['codex'], self.home, self.repo, **kwargs)

    def test_codex_copies_skills_and_appends_toml(self):
        self.write(self.toml, 'model = "example"\r\n[mcp_servers.other]\r\ncommand = "other"\r\n')
        original = self.toml.read_bytes()
        self.run_install()
        self.assertEqual((self.home / '.agents/skills/chords/SKILL.md').read_bytes(), (self.skill / 'SKILL.md').read_bytes())
        self.assertTrue(self.toml.read_bytes().startswith(original))
        self.assertIn('[mcp_servers.soundcraft]', self.toml.read_text())
        self.assertIn('command = "soundcraft-cli"', self.toml.read_text())
        self.assertIn('args = ["mcp"]', self.toml.read_text())

    def test_idempotent(self):
        self.write(self.toml, '# Existing config\n')
        self.run_install()
        before = self.snapshot()
        self.run_install(['codex', 'codex'])
        self.assertEqual(self.snapshot(), before)
        self.assertEqual(self.toml.read_text().count('[mcp_servers.soundcraft]'), 1)
        self.assertEqual(len(list(self.toml.parent.glob('config.toml.bak-*'))), 1)

    def test_backup_before_edit(self):
        self.write(self.toml, 'model = "example"\r\n')
        original = self.toml.read_bytes()
        self.run_install()
        backups = list(self.toml.parent.glob('config.toml.bak-*'))
        self.assertEqual(len(backups), 1)
        self.assertEqual(backups[0].read_bytes(), original)

    def test_backups_do_not_collide(self):
        with patch.object(self.installer, '_backup_stamp', return_value='20261025120000'):
            self.write(self.toml, '# First config\n')
            self.run_install()
            self.write(self.toml, '# Second config\n')
            self.run_install()
        self.assertEqual({p.read_text() for p in self.toml.parent.glob('config.toml.bak-*')},
                         {'# First config\n', '# Second config\n'})

    def test_antigravity_merges_json(self):
        data = {'theme': 'dark', 'mcpServers': {'other': {'command': 'other', 'args': ['serve']}}}
        self.write(self.json, json.dumps(data))
        original = self.json.read_bytes()
        self.run_install(['antigravity'])
        updated = json.loads(self.json.read_text())
        self.assertEqual(updated['theme'], 'dark')
        self.assertEqual(updated['mcpServers']['other'], data['mcpServers']['other'])
        self.assertEqual(updated['mcpServers']['soundcraft'], {'command': 'soundcraft-cli', 'args': ['mcp']})
        self.assertTrue((self.home / '.gemini/config/skills/chords/SKILL.md').is_file())
        self.assertEqual(next(self.json.parent.glob('mcp_config.json.bak-*')).read_bytes(), original)
        before = self.snapshot()
        self.run_install(['antigravity'])
        self.assertEqual(self.snapshot(), before)

    def test_dry_run_writes_nothing(self):
        for existing in (False, True):
            with self.subTest(existing=existing):
                if existing:
                    self.write(self.toml, '# Keep\n')
                    self.write(self.json, '{"mcpServers":{"other":{"command":"other"}}}')
                before = self.snapshot()
                lines = self.run_install(['codex', 'antigravity'], dry_run=True, link=True)
                self.assertTrue(lines)
                self.assertEqual(self.snapshot(), before)
                self.assertEqual(self.home.exists(), existing)

    def test_different_soundcraft_config_is_actionable_conflict(self):
        for path, content, target in (
            (self.toml, '[mcp_servers.soundcraft]\ncommand = "custom"\n', 'codex'),
            (self.json, '{"mcpServers":{"soundcraft":{"command":"custom"}}}', 'antigravity'),
        ):
            with self.subTest(target=target):
                self.write(path, content)
                before = self.snapshot()
                with self.assertRaisesRegex(ValueError, '(?i)conflict.*soundcraft.*(move|remove|rename|resolve)'):
                    self.run_install([target])
                self.assertEqual(self.snapshot(), before)

    def test_quoted_inline_and_nested_toml_server_definitions_are_not_duplicated(self):
        for content in (
            '[mcp_servers."soundcraft"]\ncommand = "custom"\n',
            "['mcp_servers'.'soundcraft']\ncommand = 'custom'\n",
            '[mcp_servers.soundcraft.env]\nX = "y"\n',
            '[mcp_servers]\nsoundcraft = {command="custom"}\n',
            'mcp_servers = { soundcraft = {command="custom"} }\n',
        ):
            with self.subTest(content=content):
                self.write(self.toml, content)
                before = self.snapshot()
                with self.assertRaisesRegex(ValueError, '(?i)conflict'):
                    self.run_install()
                self.assertEqual(self.snapshot(), before)

    def test_existing_different_skill_is_not_overwritten(self):
        dest = self.home / '.agents/skills/chords/SKILL.md'
        self.write(dest, 'Caller-owned skill')
        before = self.snapshot()
        with self.assertRaisesRegex(ValueError, '(?i)conflict.*chords'):
            self.run_install()
        self.assertEqual(self.snapshot(), before)

    def test_multiline_toml_cannot_hide_soundcraft_before_any_writes(self):
        for quote in ('"""', "'''"):
            for definition in (
                'mcp_servers.soundcraft.command = "custom"',
                'mcp_servers = { soundcraft = { command = "custom" } }',
            ):
                with self.subTest(quote=quote, definition=definition):
                    content = 'model_instructions = ' + quote + '\n[example]\n' + quote + '\n' + definition + '\n'
                    self.write(self.toml, content)
                    before = self.snapshot()
                    for dry_run in (False, True):
                        with self.assertRaisesRegex(ValueError, '(?i)conflict.*(multiline|soundcraft)'):
                            self.run_install(['antigravity', 'codex'], dry_run=dry_run)
                        self.assertEqual(self.snapshot(), before)

    def test_link_fallback_is_safe_and_idempotent(self):
        with patch.object(Path, 'symlink_to', side_effect=OSError('Privilege unavailable')):
            lines = self.run_install(link=True)
        self.assertTrue(any('warning' in line.lower() and 'copy' in line.lower() for line in lines))
        self.assertTrue((self.home / '.agents/skills/chords/SKILL.md').is_file())
        before = self.snapshot()
        self.run_install(link=True)
        self.assertEqual(self.snapshot(), before)

    def make_link(self, dest, source):
        dest.parent.mkdir(parents=True, exist_ok=True)
        try:
            dest.symlink_to(source, target_is_directory=True)
        except OSError as exc:
            self.skipTest('Native symlinks unavailable: ' + str(exc))

    def test_existing_correct_link_is_unchanged(self):
        dest = self.home / '.agents/skills/chords'
        self.make_link(dest, self.skill)
        self.run_install(link=True)
        self.run_install(link=True)
        self.assertTrue(dest.is_symlink())
        self.assertEqual(dest.resolve(), self.skill.resolve())

    def test_existing_different_or_broken_link_is_not_deleted(self):
        dest = self.home / '.agents/skills/chords'
        source = self.root / 'missing caller path'
        self.make_link(dest, source)
        original_target = dest.readlink()
        with self.assertRaisesRegex(ValueError, '(?i)conflict'):
            self.run_install(link=True)
        self.assertTrue(dest.is_symlink())
        self.assertEqual(dest.readlink(), original_target)
        self.assertFalse(self.toml.exists())

    def test_symlinked_destination_parent_cannot_write_outside_home(self):
        outside = self.root / 'caller skills'
        outside.mkdir()
        self.make_link(self.home / '.agents/skills', outside)
        with self.assertRaisesRegex(ValueError, '(?i)(conflict|outside|symlink)'):
            self.run_install()
        self.assertEqual(list(outside.iterdir()), [])

    def test_malformed_json_is_rejected_before_any_target_writes(self):
        for content in ('{broken', '[]', '{"mcpServers":[]}', '{"mcpServers":null}',
                        '{"mcpServers":{"soundcraft":{"command":"custom"}},"mcpServers":{}}',
                        '{"mcpServers":{"soundcraft":{"command":"custom"},"soundcraft":{"command":"soundcraft-cli","args":["mcp"]}}}'):
            with self.subTest(content=content):
                self.write(self.json, content)
                before = self.snapshot()
                with self.assertRaises(ValueError):
                    self.run_install(['codex', 'antigravity'])
                self.assertEqual(self.snapshot(), before)

    def test_backup_failure_does_not_edit_config(self):
        self.write(self.toml, '# Caller config\n')
        with patch.object(self.installer, '_backup', side_effect=OSError('Backup disk full')):
            with self.assertRaisesRegex(OSError, 'Backup disk full'):
                self.run_install()
        self.assertEqual(self.toml.read_bytes(), b'# Caller config\n')

    def test_source_symlink_is_not_followed(self):
        self.make_link(self.skill / 'caller link', self.root / 'missing')
        with self.assertRaisesRegex(ValueError, '(?i)(link|redirected)'):
            self.run_install()
        self.assertFalse(self.home.exists())

    def test_post_backup_config_symlink_cannot_redirect_write(self):
        for target, config, original in (
            ('codex', self.toml, b'# Original\n'),
            ('antigravity', self.json, b'{"theme":"original"}\n'),
        ):
            with self.subTest(target=target):
                self.write(config, original.decode())
                outside = self.root / ('caller-' + target)
                outside.write_bytes(original)
                backup = self.installer._backup

                def substitute(path, data):
                    result = backup(path, data)
                    path.unlink()
                    try:
                        path.symlink_to(outside)
                    except OSError as exc:
                        self.skipTest('Native symlinks unavailable: ' + str(exc))
                    return result

                with patch.object(self.installer, '_backup', substitute):
                    with self.assertRaisesRegex(ValueError, '(?i)(conflict|changed|link)'):
                        self.run_install([target])
                self.assertEqual(outside.read_bytes(), original)
                self.assertTrue(config.is_symlink())
                self.assertEqual(next(config.parent.glob(config.name + '.bak-*')).read_bytes(), original)

    def test_post_backup_parent_redirection_cannot_write_outside_home(self):
        self.write(self.toml, '# Original\n')
        outside = self.root / 'caller directory'
        outside.mkdir()
        caller_config = outside / self.toml.name
        caller_config.write_bytes(b'# Original\n')
        backup = self.installer._backup
        moved = self.root / 'original codex directory'

        def substitute(path, data):
            result = backup(path, data)
            path.parent.rename(moved)
            self.make_link(path.parent, outside)
            return result

        with patch.object(self.installer, '_backup', substitute):
            with self.assertRaisesRegex(ValueError, '(?i)(conflict|redirect|parent)'):
                self.run_install()
        self.assertEqual(caller_config.read_bytes(), b'# Original\n')
        self.assertEqual(sorted(p.name for p in outside.iterdir()), ['config.toml'])
        self.assertEqual((moved / self.toml.name).read_bytes(), b'# Original\n')
        self.assertEqual(next(moved.glob('config.toml.bak-*')).read_bytes(), b'# Original\n')

    def test_post_backup_replaced_or_modified_config_is_preserved(self):
        for change in ('identity', 'content'):
            with self.subTest(change=change):
                self.write(self.toml, '# Original\n')
                backup = self.installer._backup

                def substitute(path, data):
                    result = backup(path, data)
                    if change == 'identity':
                        replacement = self.root / 'replacement'
                        replacement.write_bytes(data)
                        replacement.replace(path)
                    else:
                        path.write_bytes(b'# Concurrent edit\n')
                    return result

                with patch.object(self.installer, '_backup', substitute):
                    with self.assertRaisesRegex(ValueError, '(?i)(conflict|changed)'):
                        self.run_install()
                expected = b'# Original\n' if change == 'identity' else b'# Concurrent edit\n'
                self.assertEqual(self.toml.read_bytes(), expected)

    def test_config_appearing_after_preflight_is_preserved(self):
        copytree = self.installer.shutil.copytree

        def copy_then_create(*args, **kwargs):
            result = copytree(*args, **kwargs)
            self.write(self.toml, '')
            return result

        with patch.object(self.installer.shutil, 'copytree', copy_then_create):
            with self.assertRaisesRegex(ValueError, '(?i)(conflict|changed|appeared)'):
                self.run_install()
        self.assertEqual(self.toml.read_bytes(), b'')
        self.assertEqual(list(self.toml.parent.glob('config.toml.bak-*')), [])

    def test_atomic_replace_failure_preserves_config_and_removes_temporary(self):
        self.write(self.toml, '# Original\n')
        with patch('os.replace', side_effect=OSError('Replace unavailable')):
            with self.assertRaisesRegex(OSError, 'Replace unavailable'):
                self.run_install()
        self.assertEqual(self.toml.read_bytes(), b'# Original\n')
        self.assertEqual(next(self.toml.parent.glob('config.toml.bak-*')).read_bytes(), b'# Original\n')
        self.assertEqual(list(self.toml.parent.glob('.*.tmp-*')), [])

    def test_last_moment_config_link_is_replaced_without_following_it(self):
        self.write(self.toml, '# Original\n')
        outside = self.root / 'caller at replace'
        outside.write_bytes(b'# Caller\n')
        replace = os.replace

        def substitute(source, destination, **kwargs):
            self.toml.unlink()
            try:
                self.toml.symlink_to(outside)
            except OSError as exc:
                self.skipTest('Native symlinks unavailable: ' + str(exc))
            return replace(source, destination, **kwargs)

        with patch('os.replace', substitute):
            self.run_install()
        self.assertEqual(outside.read_bytes(), b'# Caller\n')
        self.assertFalse(self.toml.is_symlink())
        self.assertIn('[mcp_servers.soundcraft]', self.toml.read_text())

    def test_last_moment_parent_redirection_cannot_redirect_replace(self):
        self.write(self.toml, '# Original\n')
        outside = self.root / 'caller at parent replace'
        outside.mkdir()
        caller = outside / self.toml.name
        caller.write_bytes(b'# Caller\n')
        moved = self.root / 'moved at replace'
        replace = os.replace

        def substitute(source, destination, **kwargs):
            try:
                self.toml.parent.rename(moved)
            except PermissionError:
                # Windows directory handles deny renames during the commit.
                if os.name != 'nt':
                    raise
            else:
                self.make_link(self.toml.parent, outside)
            return replace(source, destination, **kwargs)

        with patch('os.replace', substitute):
            self.run_install()
        self.assertEqual(caller.read_bytes(), b'# Caller\n')
        actual = moved / self.toml.name if moved.exists() else self.toml
        self.assertIn('[mcp_servers.soundcraft]', actual.read_text())
        self.assertEqual(list(actual.parent.glob('.*.tmp-*')), [])

    def test_symlinked_config_is_not_followed(self):
        outside = self.root / 'caller config'
        outside.write_bytes(b'# Caller config\n')
        self.toml.parent.mkdir(parents=True)
        try:
            self.toml.symlink_to(outside)
        except OSError as exc:
            self.skipTest('Native symlinks unavailable: ' + str(exc))
        with self.assertRaisesRegex(ValueError, '(?i)conflict'):
            self.run_install()
        self.assertEqual(outside.read_bytes(), b'# Caller config\n')
        self.assertFalse((self.home / '.agents').exists())

    def test_failed_link_does_not_copy_into_new_caller_destination(self):
        dest = self.home / '.agents/skills/chords'
        def create_then_fail(path, target, **kwargs):
            path.mkdir()
            (path / 'caller.txt').write_text('Keep', encoding='utf-8')
            raise OSError('Destination appeared')
        with patch.object(Path, 'symlink_to', create_then_fail):
            with self.assertRaisesRegex(ValueError, '(?i)conflict'):
                self.run_install(link=True)
        self.assertEqual((dest / 'caller.txt').read_text(), 'Keep')
        self.assertFalse((dest / 'SKILL.md').exists())
        self.assertFalse(self.toml.exists())

    def test_unknown_target_and_missing_skills_do_not_write(self):
        with self.assertRaisesRegex(ValueError, '(?i)target'):
            self.run_install(['claude'])
        with self.assertRaisesRegex(ValueError, '(?i)skills'):
            self.installer.install(['codex'], self.home, self.root / 'missing repo')
        self.assertFalse(self.home.exists())

    def test_cli_help_and_dry_run(self):
        help_run = subprocess.run([sys.executable, str(SCRIPT)], capture_output=True, text=True)
        self.assertEqual(help_run.returncode, 0, help_run.stderr)
        self.assertIn('--all', help_run.stdout)
        self.assertIn('/plugin marketplace add', help_run.stdout)
        # Call main with a fake __file__ and home: CLI probes never use real homes/repo.
        with patch.object(self.installer, '__file__', str(self.repo / 'install.py')), patch.object(Path, 'home', return_value=self.home), redirect_stdout(io.StringIO()):
            self.assertEqual(self.installer.main(['--all', '--dry-run', '--link']), 0)
        self.assertFalse(self.home.exists())
