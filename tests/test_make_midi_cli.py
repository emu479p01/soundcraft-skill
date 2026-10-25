from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from scmidi.midi_reader import read_smf

CORE = Path(__file__).resolve().parent.parent / "skills" / "soundcraft-core"
SCRIPT = CORE / "scripts" / "make_midi.py"
EXAMPLE = CORE / "examples" / "lofi-sketch.json"


def _cli(*args: str, stdin: str | None = None) -> subprocess.CompletedProcess:
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    return subprocess.run([sys.executable, str(SCRIPT), *args], input=stdin,
                          capture_output=True, text=True, encoding="utf-8", env=env)


class MakeMidiCliTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)

    def test_cli_writes_and_prints_summary(self):
        out = self.tmp / "sketch.mid"
        result = _cli(str(EXAMPLE), "--out", str(out))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Bar 1: Dm9 = ", result.stdout)
        self.assertIn(f"Wrote: {out.resolve()}", result.stdout)
        song = read_smf(out)
        self.assertEqual({t.channel for t in song.tracks}, {0, 9})

    def test_cli_default_output_next_to_spec(self):
        spec = self.tmp / "my song.json"
        spec.write_text(json.dumps({"tracks": [{"type": "chords", "progression": "C"}]}),
                        encoding="utf-8")
        result = _cli(str(spec))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((self.tmp / "my song.mid").is_file())

    def test_cli_spec_output_relative_to_spec(self):
        spec = self.tmp / "a.json"
        spec.write_text(json.dumps({"output": "sub/b.mid", "tracks": [
            {"type": "chords", "progression": "C"}]}), encoding="utf-8")
        result = _cli(str(spec))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((self.tmp / "sub" / "b.mid").is_file())

    def test_cli_invalid_exit2(self):
        spec = self.tmp / "bad.json"
        spec.write_text(json.dumps({"tracks": [
            {"type": "chords", "progression": ["C"], "voiceing": "open"}]}),
            encoding="utf-8")
        result = _cli(str(spec))
        self.assertEqual(result.returncode, 2)
        self.assertIn("tracks[0].voiceing", result.stderr)
        self.assertEqual(sorted(p.name for p in self.tmp.iterdir()), ["bad.json"])

    def test_cli_extreme_numbers_exit2_with_field_path(self):
        cases = [
            ({"tracks": [{"type": "chords", "progression": [
                {"chord": "C", "beats": 1e308}]}]},
             "tracks[0].progression[0].beats"),
            ({"tracks": [{"type": "chords", "progression": ["C"],
                           "chord_length": "9" * 309 + "beats"}]},
             "tracks[0].chord_length"),
            ({"bpm": 10 ** 400, "tracks": [
                {"type": "chords", "progression": ["C"]}]}, "bpm"),
        ]
        for raw, path in cases:
            with self.subTest(path=path):
                result = _cli("-", "--out", str(self.tmp / "invalid.mid"),
                              stdin=json.dumps(raw))
                self.assertEqual(result.returncode, 2, result.stderr)
                self.assertIn(path, result.stderr)
                self.assertFalse((self.tmp / "invalid.mid").exists())

    def test_cli_encodes_all_rest_custom_chord_track(self):
        out = self.tmp / "silent.mid"
        raw = {"tracks": [{"type": "chords", "progression": ["C"],
                           "rhythm": "custom", "steps": "." * 16}]}
        result = _cli("-", "--out", str(out), stdin=json.dumps(raw))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(out.is_file())
        song = read_smf(out)
        self.assertFalse(any(track.notes for track in song.tracks))

    def test_cli_invalid_json_exit2(self):
        result = _cli("-", "--out", str(self.tmp / "x.mid"), stdin="{not json")
        self.assertEqual(result.returncode, 2)
        self.assertIn("JSON", result.stderr)
        self.assertFalse((self.tmp / "x.mid").exists())

    def test_cli_missing_spec_exit1(self):
        result = _cli(str(self.tmp / "nope.json"))
        self.assertEqual(result.returncode, 1)
        self.assertIn("nope.json", result.stderr)

    def test_cli_json_output(self):
        out = self.tmp / "j.mid"
        result = _cli(str(EXAMPLE), "--out", str(out), "--json")
        self.assertEqual(result.returncode, 0, result.stderr)
        data = json.loads(result.stdout)
        self.assertEqual(data["output"], str(out.resolve()))
        chords, drums = data["tracks"]
        self.assertEqual(chords["name"], "Chords")
        self.assertEqual(chords["bars"][0]["bar"], 1)
        self.assertEqual(chords["bars"][0]["chord"], "Dm9")
        self.assertEqual(len(chords["bars"][0]["notes"]), 5)
        self.assertEqual(drums["bars"][0], {"bar": 1, "hits": {"kick": 3, "snare": 3,
                                                               "hat": 8}})

    def test_cli_stdin_and_unicode_out(self):
        out = self.tmp / "เพลง ใหม่" / "ทดสอบ.mid"
        spec = json.dumps({"tracks": [{"type": "chords", "progression": "C - G"}]})
        result = _cli("-", "--out", str(out), stdin=spec)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(out.is_file())
        self.assertIn("ทดสอบ.mid", result.stdout)


if __name__ == "__main__":
    unittest.main()
