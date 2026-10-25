"""Actual eight-skill copies into two temporary fake homes; no native loading."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import re
import tempfile
import unittest


REPO = Path(__file__).resolve().parents[1]


class InstalledGuidanceTests(unittest.TestCase):
    def test_actual_package_links_and_runtime_recovery_in_both_homes(self):
        spec = importlib.util.spec_from_file_location("package_installer", REPO / "install.py")
        installer = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(installer)
        with tempfile.TemporaryDirectory() as tmp:
            for target, layout in (("codex", ".agents/skills"),
                                   ("antigravity", ".gemini/config/skills")):
                with self.subTest(target=target):
                    home = Path(tmp) / (target + " fake home")
                    installer.install([target], home, REPO)
                    root = home / layout
                    self.assertEqual(len(list(root.glob("*/SKILL.md"))), 8)
                    self.assertTrue((root / "soundcraft-core/scripts/make_midi.py").is_file())
                    missing = []
                    for path in root.rglob("*.md"):
                        for link in re.findall(r"\]\(([^)]+)\)", path.read_text(encoding="utf-8")):
                            if "://" not in link and not link.startswith("#"):
                                if not (path.parent / link.split("#", 1)[0]).is_file():
                                    missing.append(str(path.relative_to(root)) + " -> " + link)
                    self.assertEqual(missing, [])
                    setup = (root / "soundcraft-setup/SKILL.md").read_text(encoding="utf-8")
                    runtime = root / "soundcraft-core/references/harness-setup.md"
                    self.assertTrue(runtime.is_file(), "MCP recovery must ship inside copied skills")
                    self.assertIn("../soundcraft-core/references/harness-setup.md", setup)
                    guidance = runtime.read_text(encoding="utf-8")
                    self.assertIn("source-checkout-only", setup.lower())
                    self.assertIn("user-provided", guidance.lower())
                    self.assertNotIn("../../install.py", setup + guidance)
                    self.assertNotIn("../../docs/", setup + guidance)
                    for required in ("~/.codex/config.toml", "[mcp_servers.soundcraft]",
                                     "~/.gemini/config/mcp_config.json", '"mcpServers"',
                                     "claude mcp add soundcraft", "list_commands",
                                     "--automation-read-root", "--automation-write-root"):
                        self.assertIn(required, guidance)
