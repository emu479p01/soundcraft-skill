"""Lint skill entrypoints and embedded MIDI specs (stdlib, Python 3.9+).

Relative script paths in entrypoints and references are relative to the skill
directory. Frontmatter supports scalar fields and an indented metadata mapping;
this deliberately small parser is not a general YAML implementation.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys


REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "skills" / "soundcraft-core" / "scripts"))
from scmidi.spec import SpecError, validate_spec


SECTIONS = ["When to use", "Workflow", "Style table", "Spec pattern", "Checks",
            "Limits", "Related skills"]
FIELDS = {"name", "description", "license", "metadata"}
SCRIPT_PATH = re.compile(
    r"(?<![\w./:\\-])(?:\.\./soundcraft-core/)?scripts/"
    r"[^\s`\"'()\[\]]+")
FENCE = re.compile(r"^ {0,3}(`{3,}|~{3,})(.*)$")


def _scalar(value: str) -> str:
    """Decode plain, single-quoted or double-quoted scalar text and comments."""
    value = value.strip()
    if value.startswith('"'):
        decoded, end = json.JSONDecoder().raw_decode(value)
        if not isinstance(decoded, str):
            raise ValueError("expected a string")
        tail = value[end:].strip()
        if tail and not tail.startswith("#"):
            raise ValueError("unexpected text after quoted value")
        return decoded
    if value.startswith("'"):
        parts = []
        i = 1
        while i < len(value):
            if value[i] == "'":
                if i + 1 < len(value) and value[i + 1] == "'":
                    parts.append("'")
                    i += 2
                    continue
                tail = value[i + 1:].strip()
                if tail and not tail.startswith("#"):
                    raise ValueError("unexpected text after quoted value")
                return "".join(parts)
            parts.append(value[i])
            i += 1
        raise ValueError("unterminated quoted value")
    return re.split(r"\s+#", value, maxsplit=1)[0].rstrip()


def _frontmatter(lines: list[str], path: Path, skill_dir: Path,
                 errors: list[str]) -> int:
    if not lines or lines[0] != "---":
        errors.append(f"{path}:1: missing frontmatter opening ---")
        return 0
    try:
        end = lines.index("---", 1)
    except ValueError:
        errors.append(f"{path}:1: missing frontmatter closing ---")
        return 0
    fields = {}
    current = None
    for number, line in enumerate(lines[1:end], 2):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if line[0].isspace() and current == "metadata":
            continue
        match = re.fullmatch(r"([a-zA-Z_][\w-]*):\s*(.*)", line)
        if not match:
            errors.append(f"{path}:{number}: expected frontmatter key: value")
            continue
        current, value = match.groups()
        if current not in FIELDS:
            errors.append(f"{path}:{number}: unsupported frontmatter field {current!r}")
        if current in fields:
            errors.append(f"{path}:{number}: duplicate frontmatter field {current!r}")
        try:
            fields[current] = _scalar(value)
        except ValueError as exc:
            errors.append(f"{path}:{number}: {current}: {exc}")
            fields[current] = ""
    name = fields.get("name", "")
    if (name != skill_dir.name or len(name) > 64
            or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", name)):
        errors.append(f"{path}:1: name must match folder {skill_dir.name!r}, be at most "
                      "64 characters, and use lowercase letters, digits and single hyphens")
    description = fields.get("description", "")
    if not description.strip() or len(description) > 1024:
        errors.append(f"{path}:1: description must contain 1-1024 characters")
    return end + 1


def _json_spec(content: list[str], path: Path, start: int, errors: list[str]) -> None:
    try:
        raw = json.loads("\n".join(content))
    except json.JSONDecodeError as exc:
        # Parsing every JSON fence catches broken intended specs, including escaped
        # keys and syntax errors before the tracks field. Valid unrelated JSON is OK.
        errors.append(f"{path}:{start + exc.lineno - 1}: invalid JSON "
                      f"(column {exc.colno}): {exc.msg}")
        return
    if isinstance(raw, dict) and "tracks" in raw:
        try:
            validate_spec(raw)
        except SpecError as exc:
            errors.append(f"{path}:{start}: invalid spec: {exc}")


def _document(text: str, path: Path, skill_dir: Path, offset: int,
              errors: list[str]) -> list[str]:
    headings = []
    fence = None
    content = []
    start = 0
    language = ""
    for number, line in enumerate(text.splitlines()[offset:], offset + 1):
        for match in SCRIPT_PATH.finditer(line):
            reference = match.group().rstrip(".,;:")
            # Skip documentation templates as whole tokens, never partial paths.
            if any(char in reference for char in "<>*?{}$") or reference.endswith("/"):
                continue
            if not (skill_dir / reference).is_file():
                errors.append(f"{path}:{number}: script reference does not exist: {reference}")
        match = FENCE.match(line)
        if fence is not None:
            if (match and match[1][0] == fence[0] and len(match[1]) >= len(fence)
                    and not match[2].strip()):
                if language == "json":
                    _json_spec(content, path, start, errors)
                fence = None
            else:
                content.append(line)
            continue
        if match:
            fence = match[1]
            language = match[2].strip().lower()
            content = []
            start = number + 1
            continue
        heading = re.match(r"^ {0,3}##\s+(.+?)\s*$", line)
        if heading:
            headings.append(re.sub(r"\s+#+$", "", heading[1]))
    if fence is not None and language == "json":
        errors.append(f"{path}:{start - 1}: unclosed JSON fence; add matching {fence}")
    return headings


def lint_skill(skill_dir: Path) -> list[str]:
    """Return actionable errors for one skill and its reference documents."""
    skill_dir = Path(skill_dir)
    path = skill_dir / "SKILL.md"
    errors: list[str] = []
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        return [f"{path}: cannot read SKILL.md: {exc}"]
    offset = _frontmatter(text.splitlines(), path, skill_dir, errors)
    if _document(text, path, skill_dir, offset, errors) != SECTIONS:
        errors.append(f"{path}: sections must be exactly these seven H2s in order: "
                      + " -> ".join(SECTIONS))
    references = skill_dir / "references"
    if references.is_dir():
        for reference in sorted(references.rglob("*")):
            if reference.is_file():
                try:
                    text = reference.read_text(encoding="utf-8")
                except (OSError, UnicodeError) as exc:
                    errors.append(f"{reference}: cannot read reference: {exc}")
                    continue
                _document(text, reference, skill_dir, 0, errors)
    return errors


def lint_all(repo: Path) -> dict[str, list[str]]:
    """Lint only immediate skills/* directories with an existing SKILL.md."""
    return {path.parent.name: lint_skill(path.parent)
            for path in sorted((Path(repo) / "skills").glob("*/SKILL.md"))
            if path.is_file()}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("skill_dirs", nargs="*", type=Path)
    args = parser.parse_args(argv)
    results = ({str(path): lint_skill(path) for path in args.skill_dirs}
               if args.skill_dirs else lint_all(REPO))
    errors = [error for group in results.values() for error in group]
    for error in errors:
        print(error)
    if errors:
        print(f"FAILED: {len(errors)} error(s)")
        return 1
    print(f"OK: {len(results)} skill(s) checked")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
