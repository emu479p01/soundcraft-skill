"""Behavioral checks for skill documentation linting."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "tools" / "lint_skills.py"
HEADINGS = ("When to use", "Workflow", "Style table", "Spec pattern", "Checks",
            "Limits", "Related skills")
VALID = {"tracks": [{"type": "chords", "progression": ["C", "G"]}]}


class SkillLintTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.assertTrue(SCRIPT.is_file(), "Task 10 linter must exist")
        spec = importlib.util.spec_from_file_location("skill_linter", SCRIPT)
        self.linter = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.linter)

    def skill(self, name="chords", front=None, body=""):
        folder = self.root / "skills" / name
        folder.mkdir(parents=True, exist_ok=True)
        if front is None:
            front = f"name: {name}\ndescription: Make music.\n"
        text = "---\n" + front + "---\n"
        text += "\n".join("## " + h for h in HEADINGS) + "\n" + body
        (folder / "SKILL.md").write_text(text, encoding="utf-8")
        return folder

    def test_lint_flags_bad_fixture(self):
        folder = self.skill(body='`scripts/missing.py`\n```json\n{"tracks": []}\n```\n')
        path = folder / "SKILL.md"
        path.write_text(path.read_text().replace("name: chords", "name: Bad_Name")
                        .replace("## Limits\n", ""), encoding="utf-8")
        errors = self.linter.lint_skill(folder)
        self.assertEqual(len(errors), 4, errors)
        for fragment in ("name", "sections", "missing.py", "tracks"):
            self.assertTrue(any(fragment in e for e in errors), errors)

    def test_valid_cross_skill_and_nested_references(self):
        folder = self.skill(body='`scripts/local.py` and '
                            '[renderer](../soundcraft-core/scripts/make_midi.py).\n'
                            'Placeholders: `scripts/<file>`, `scripts/*.py`, '
                            '`../soundcraft-core/scripts/<name>.py`.\n'
                            'Unrelated `other/scripts/no.py` and https://x/scripts/no.py.\n'
                            '```json\n{"result": {"tracks": []}}\n```\n'
                            '```text\n## Not a section\n```\n')
        for path in (folder / "scripts/local.py",
                     folder.parent / "soundcraft-core/scripts/make_midi.py"):
            path.parent.mkdir(parents=True, exist_ok=True)
            path.touch()
        ref = folder / "references/nested/examples.md"
        ref.parent.mkdir(parents=True)
        ref.write_text('Use `scripts/local.py`.\n```json\n' + json.dumps(VALID)
                       + '\n```\n', encoding="utf-8")
        self.assertEqual(self.linter.lint_skill(folder), [])
        ref.write_text('```json\n{"tracks": []}\n```\n', encoding="utf-8")
        errors = self.linter.lint_skill(folder)
        self.assertEqual(len(errors), 1, errors)
        self.assertIn("examples.md:2", errors[0])
        self.assertIn("tracks", errors[0])

    def test_malformed_json_is_actionable(self):
        for block in ('{"tracks": [}', '{\n"bpm": 90,\n"tracks": [],\n}',
                      '{"tracks": []} trailing', '{"tr\\u0061cks": [}'):
            with self.subTest(block=block):
                folder = self.skill(body="```json\n" + block + "\n```\n")
                errors = self.linter.lint_skill(folder)
                self.assertEqual(len(errors), 1, errors)
                self.assertRegex(errors[0], r"SKILL\.md:\d+:.*JSON")

    def test_unclosed_json_fence(self):
        folder = self.skill(body='```json\n{"tracks": []}\n')
        self.assertTrue(any("unclosed" in e for e in self.linter.lint_skill(folder)))

    def test_extensionless_scripts_and_placeholder_suffixes(self):
        folder = self.skill(body='Run `scripts/check`. Templates: `scripts/example_*.py`, '
                            '`scripts/name{variant}.py`, `scripts/<file>.py`.\n')
        errors = self.linter.lint_skill(folder)
        self.assertEqual(len(errors), 1, errors)
        self.assertIn("scripts/check", errors[0])
        (folder / "scripts").mkdir()
        (folder / "scripts/check").touch()
        self.assertEqual(self.linter.lint_skill(folder), [])

    def test_frontmatter_rules_and_quoted_descriptions(self):
        for description in ('"Music: use #1"', "'It''s music: #1'", 'Music # comment'):
            folder = self.skill(front="name: 'chords'\ndescription: " + description
                                + "\nlicense: MIT\nmetadata:\n  author: Composer\n")
            self.assertEqual(self.linter.lint_skill(folder), [])
        for front, fragment in (
                ("name: other\ndescription: Fine\n", "name"),
                ("name: chords\ndescription: " + "a" * 1025 + "\n", "description"),
                ("name: chords\ndescription: Fine\nauthor: Someone\n", "author"),
                ("name: chords\n", "description"),
                ('name: chords\ndescription: "unterminated\n', "description"),
                ("name: chords\nname: chords\ndescription: Fine\n", "duplicate")):
            folder = self.skill(front=front)
            self.assertTrue(any(fragment in e for e in self.linter.lint_skill(folder)))

    def test_extra_reordered_and_duplicate_sections(self):
        for replacement in ("## Limits\n## Checks", "## Checks\n## Checks",
                            "## Checks\n## Extra\n## Limits"):
            folder = self.skill()
            path = folder / "SKILL.md"
            path.write_text(path.read_text().replace("## Checks\n## Limits", replacement))
            self.assertTrue(any("sections" in e for e in self.linter.lint_skill(folder)))

    def test_closing_heading_hashes_require_whitespace(self):
        for heading, valid in (("Checks", True), ("Checks ###", True),
                               ("Checks\t###", True), ("Checks###", False)):
            with self.subTest(heading=heading):
                folder = self.skill()
                path = folder / "SKILL.md"
                path.write_text(path.read_text().replace("## Checks\n", "## " + heading + "\n"),
                                encoding="utf-8")
                errors = self.linter.lint_skill(folder)
                self.assertEqual(any("sections" in e for e in errors), not valid, errors)

    def test_lint_all_ignores_directories_without_skill(self):
        self.skill()
        (self.root / "skills/unfinished").mkdir()
        self.assertEqual(self.linter.lint_all(self.root), {"chords": []})

    def test_cli_isolated_from_other_cwd(self):
        folder = self.skill()
        result = subprocess.run([sys.executable, "-I", str(SCRIPT), str(folder)],
                                cwd=self.root, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertIn("OK", result.stdout)
        result = subprocess.run([sys.executable, "-I", str(SCRIPT), str(folder),
                                 str(self.root / "missing")], cwd=self.root,
                                capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("SKILL.md", result.stdout + result.stderr)
        result = subprocess.run([sys.executable, "-I", str(SCRIPT)], cwd=self.root,
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)

    def test_repo_skills_clean(self):
        results = self.linter.lint_all(REPO)
        if not results:
            self.skipTest("No SKILL.md entrypoints have been authored yet")
        self.assertFalse({name: errors for name, errors in results.items() if errors})
