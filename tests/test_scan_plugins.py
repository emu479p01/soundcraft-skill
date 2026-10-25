"""Plugin inventory tests; all filesystem changes stay in temporary trees."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime
from unittest.mock import patch

import scan_plugins


SCRIPT = Path(__file__).resolve().parents[1] / "skills/soundcraft-core/scripts/scan_plugins.py"


class ScannerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def touch(self, name):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.touch()
        return path

    def test_default_dirs_windows(self):
        common, local, programs = (self.root / p for p in ("Common", "Local", "Programs"))
        dirs = scan_plugins.default_dirs("win32", {
            "CommonProgramFiles": str(common), "LOCALAPPDATA": str(local),
            "ProgramFiles": str(programs), "CLAP_PATH": "extra one;extra two;;"}, self.root)
        self.assertEqual(dirs, [
            (common / "VST3", "vst3"), (common / "CLAP", "clap"),
            (local / "Programs/Common/VST3", "vst3"),
            (local / "Programs/Common/CLAP", "clap"),
            (programs / "VSTPlugins", "vst2"),
            (programs / "Steinberg/VstPlugins", "vst2"), (common / "VST2", "vst2"),
            (Path("extra one"), "clap"), (Path("extra two"), "clap")])

    def test_default_dirs_linux_clap_path(self):
        self.assertEqual(scan_plugins.default_dirs("linux", {"CLAP_PATH": "/a:/b::"}, self.root), [
            (self.root / ".vst3", "vst3"), (self.root / ".clap", "clap"),
            (Path("/usr/lib/vst3"), "vst3"), (Path("/usr/local/lib/vst3"), "vst3"),
            (Path("/usr/lib/clap"), "clap"), (Path("/usr/local/lib/clap"), "clap"),
            (Path("/a"), "clap"), (Path("/b"), "clap")])

    def test_default_dirs_macos(self):
        dirs = scan_plugins.default_dirs("darwin", {}, self.root)
        self.assertEqual(dirs, [(base / name, fmt)
                               for base in (Path("/Library/Audio/Plug-Ins"),
                                            self.root / "Library/Audio/Plug-Ins")
                               for name, fmt in (("VST3", "vst3"), ("CLAP", "clap"), ("Components", "au"))])

    def test_scan_finds_bundles_without_descending(self):
        self.touch("Vital.vst3/Contents/x86_64-win/Vital.vst3")
        result = scan_plugins.scan([(self.root, "vst3")])
        self.assertEqual(result["plugins"], [{"name": "Vital", "format": "vst3",
                                            "path": str(self.root / "Vital.vst3"), "category": "synth"}])

    def test_overlapping_roots_do_not_expose_bundle_contents(self):
        inner = self.touch("Vital.vst3/Contents/nested.clap").parent
        self.touch("folder/Other.clap")
        result = scan_plugins.scan([(inner, "clap"), (self.root / "folder", "clap"),
                                    (self.root, "vst3"), (self.root / "Vital.vst3", "vst3")])
        self.assertEqual([p["name"] for p in result["plugins"]], ["Other", "Vital"])

    def test_unsupported_reported(self):
        self.touch("Old.dll")
        self.touch("X.lv2/inside.clap")
        self.touch("Y.aaxplugin/inside.clap")
        self.touch("Z.vst/inside.clap")
        result = scan_plugins.scan([(self.root, "vst2")])
        self.assertEqual(result["plugins"], [])
        self.assertEqual([(p["name"], p["format"]) for p in result["unsupported"]],
                         [("Old", "vst2"), ("X", "lv2"), ("Y", "aax"), ("Z", "vst2")])
        self.assertTrue(all(p["reason"] == "SoundCraft supports CLAP, VST3, AU only"
                            for p in result["unsupported"]))

    def test_dll_warning_only_in_designated_dirs_even_when_overlapping(self):
        self.touch("ordinary.dll")
        legacy = self.touch("legacy/Old.dll").parent
        result = scan_plugins.scan([(self.root, "auto"), (legacy, "vst2")])
        self.assertEqual([p["name"] for p in result["unsupported"]], ["Old"])

    def test_missing_dirs(self):
        missing = self.root / "missing"
        self.assertEqual(scan_plugins.scan([(missing, "clap")]),
                         {"plugins": [], "unsupported": [], "missing_dirs": [str(missing)]})

    def test_unicode_and_spaces(self):
        a = self.touch("Valhalla Supermassive.vst3")
        b = self.touch("Sérum ไทย.clap")
        self.assertEqual(scan_plugins.scan([(self.root, "auto")])["plugins"], [
            {"name": "Sérum ไทย", "format": "clap", "path": str(b), "category": "synth"},
            {"name": "Valhalla Supermassive", "format": "vst3", "path": str(a), "category": "reverb"}])

    def test_categories_first_match_and_case_folding(self):
        for name, expected in [("Drum Synth", "drum"), ("VITAL EQ", "synth"),
                               ("NOVA Comp", "eq"), ("GLUE Verb", "comp"),
                               ("Room Echo", "reverb"), ("Echo Drive", "delay"),
                               ("Tape", "saturation"), ("Piano", "other")]:
            with self.subTest(name=name):
                self.assertEqual(scan_plugins.categorize(name), expected)

    def test_case_insensitive_extensions_and_deterministic_results(self):
        self.touch("z.COMPONENT")
        self.touch("A.CLAP")
        self.touch("a.vst3")
        dirs = [(self.root, "auto"), (self.root, "clap")]
        first = scan_plugins.scan(dirs)
        self.assertEqual(first, scan_plugins.scan(list(reversed(dirs))))
        self.assertEqual([(p["name"], p["format"]) for p in first["plugins"]],
                         [("A", "clap"), ("a", "vst3"), ("z", "au")])

    def test_symlink_loop_and_alias_do_not_duplicate(self):
        folder = self.touch("folder/Helm.clap").parent
        try:
            (folder / "loop").symlink_to(self.root, target_is_directory=True)
            (self.root / "alias").symlink_to(folder, target_is_directory=True)
        except OSError as exc:
            self.skipTest(f"Directory symlinks unavailable: {exc}")
        result = scan_plugins.scan([(self.root, "auto")])
        self.assertEqual([p["name"] for p in result["plugins"]], ["Helm"])

    def cli(self, *args):
        home = self.root / "home"
        home.mkdir(exist_ok=True)
        replaced = {"home", "userprofile", "commonprogramfiles", "programfiles", "localappdata", "clap_path"}
        env = {key: value for key, value in os.environ.items() if key.casefold() not in replaced}
        env.update(HOME=str(home), USERPROFILE=str(home),
                   COMMONPROGRAMFILES=str(home / "common"), PROGRAMFILES=str(home / "programs"),
                   LOCALAPPDATA=str(home / "local"), CLAP_PATH="")
        # The managed runtime launcher can restore Windows system variables.
        # Apply fake locations inside Python before executing the real CLI.
        overrides = {key: value for key, value in env.items() if key.casefold() in replaced}
        bootstrap = ("import os, runpy, sys; os.environ.update(" + repr(overrides) + "); "
                     "sys.argv = sys.argv[1:]; runpy.run_path(sys.argv[0], run_name='__main__')")
        return subprocess.run([sys.executable, "-c", bootstrap, str(SCRIPT), *map(str, args)],
                              env=env, capture_output=True, encoding="utf-8", timeout=15)

    def test_write_corpus(self):
        self.touch("Sérum ไทย.clap")
        corpus = self.root / "output/c.json"
        result = self.cli("--extra-dir", self.root, "--json", "--write-corpus", corpus)
        self.assertEqual(result.returncode, 0, result.stderr)
        data = json.loads(corpus.read_text(encoding="utf-8"))
        self.assertIsNotNone(datetime.fromisoformat(data["scanned_at"]).tzinfo)
        self.assertEqual(data["platform"], sys.platform)
        self.assertEqual(data["plugins"][0]["name"], "Sérum ไทย")
        self.assertEqual(json.loads(result.stdout)["plugins"], data["plugins"])

    def test_default_corpus_uses_fake_home(self):
        result = self.cli("--write-corpus")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((self.root / "home/.soundcraft-skills/plugins.json").is_file())

    def test_text_groups_and_unsupported_warning(self):
        self.touch("Echo.clap")
        self.touch("Old.vst")
        result = self.cli("--extra-dir", self.root)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("delay:", result.stdout)
        self.assertIn("Echo", result.stdout)
        self.assertIn("SoundCraft supports CLAP, VST3, AU only", result.stdout)

    def test_write_failure_is_not_success(self):
        blocked = self.touch("blocked")
        result = self.cli("--write-corpus", blocked / "plugins.json")
        self.assertEqual(result.returncode, 1)
        self.assertIn("error:", result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_existing_file_root_is_error(self):
        path = self.touch("not-directory")
        result = self.cli("--extra-dir", path)
        self.assertEqual(result.returncode, 2)
        self.assertIn(str(path), result.stderr)

    def test_unreadable_tree_is_not_silently_empty(self):
        with patch("os.scandir", side_effect=PermissionError("denied")):
            with self.assertRaises(PermissionError):
                scan_plugins.scan([(self.root, "auto")])


if __name__ == "__main__":
    unittest.main()
