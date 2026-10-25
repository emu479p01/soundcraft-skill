from __future__ import annotations

import json
import math
import os
import struct
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from scmidi.model import Note, Song, Track
from scmidi.midi_reader import read_smf
from scmidi.midi_writer import write_smf
from scmidi.render import render
from scmidi.spec import validate_spec
from scmidi.theory import Key
from scmidi.analysis import detect_chords, estimate_key, name_chord, to_roman


SCRIPT = (Path(__file__).resolve().parent.parent / "skills" / "soundcraft-core"
          / "scripts" / "analyze_midi.py")


def _notes(pitches, start=0, duration=480, channel=0):
    return [Note(p, start, duration, 80, channel) for p in pitches]


def _song(notes, ppq=480, signature=(4, 4)):
    return Song(120, signature, [Track("Piano", 0, notes)], ppq)


def _progression(symbols, key="C major"):
    song, _ = render(validate_spec({"key": key, "tracks": [
        {"name": "Harmony", "type": "chords", "progression": symbols,
         "rhythm": "pad", "chord_length": "1bar", "bass_note": True}]}))
    return song


class KeyTests(unittest.TestCase):
    def test_key_c_major_scale(self):
        notes = [Note(p, i * 480, 480, 80, 0)
                 for i, p in enumerate([60, 62, 64, 65, 67, 69, 71, 72])]
        guesses = estimate_key(notes)
        self.assertEqual(guesses[0].key, Key(0, "major"))
        self.assertEqual(len({g.key for g in guesses}), 24)
        self.assertEqual([g.score for g in guesses],
                         sorted((g.score for g in guesses), reverse=True))
        self.assertTrue(all(-1 <= g.score <= 1 for g in guesses))

    def test_key_from_rendered_dm_progression(self):
        song = _progression("Dm - Gm - A7 - Dm", "D minor")
        self.assertEqual(estimate_key(song.tracks[0].notes)[0].key, Key(2, "minor"))

    def test_duration_weighted_pearson_exact_profile_and_rotation(self):
        # Durations reproduce the supplied major profile rotated to D exactly.
        durations = [635, 223, 348, 233, 438, 409, 252, 519, 239, 366, 229, 288]
        notes = [Note(60 + (pc + 2) % 12, 0, d, 1 + pc, 0)
                 for pc, d in enumerate(durations)]
        guess = estimate_key(notes)[0]
        self.assertEqual(guess.key, Key(2, "major"))
        self.assertAlmostEqual(guess.score, 1.0, places=12)

    def test_minor_profile_and_duration_split_are_invariant(self):
        durations = [633, 268, 352, 538, 260, 353, 254, 475, 398, 269, 334, 317]
        notes = [Note(60 + pc, 0, d, 80, 0) for pc, d in enumerate(durations)]
        split = [Note(n.pitch, i, 1, 1, 0) for n in notes for i in range(n.duration)]
        guesses = estimate_key(notes)
        self.assertEqual(guesses[0].key, Key(0, "minor"))
        self.assertAlmostEqual(guesses[0].score, 1.0)
        self.assertEqual(guesses, estimate_key(split))

    def test_empty_and_uniform_histograms_have_finite_zero_scores(self):
        for notes in ([], _notes(range(60, 72))):
            with self.subTest(notes=notes):
                guesses = estimate_key(notes)
                self.assertEqual(len(guesses), 24)
                self.assertTrue(all(g.score == 0.0 for g in guesses))


class ChordTests(unittest.TestCase):
    def test_name_chord(self):
        for pitches, expected in [([60, 64, 67], "C"),
                                  ([57, 60, 64, 67], "Am7"),
                                  ([59, 62, 67], "G/B"), ([60], "?"),
                                  ([], "?"), ([60, 72], "?")]:
            with self.subTest(pitches=pitches):
                symbol, score = name_chord(pitches)
                self.assertEqual(symbol, expected)
                if symbol != "?":
                    self.assertEqual(score, 1.0)

    def test_lowest_root_breaks_ambiguous_chord_ties(self):
        for pitches, symbol in [([60, 64, 67, 69], "C6"),
                                ([57, 60, 64, 67], "Am7"),
                                ([62, 67, 72], "Gsus4/D"),
                                ([60, 62, 67], "Csus2")]:
            with self.subTest(pitches=pitches):
                self.assertEqual(name_chord(pitches)[0], symbol)

    def test_chord_threshold_extra_bass_and_octave_deduplication(self):
        self.assertEqual(name_chord([60, 64])[0], "?")
        self.assertEqual(name_chord(list(range(60, 72)))[0], "?")
        symbol, score = name_chord([63, 64, 67, 72])
        self.assertEqual(symbol, "C/Eb")
        self.assertAlmostEqual(score, 5 / 6)
        self.assertEqual(name_chord([72, 67, 60, 64, 76]), ("C", 1.0))

    def test_ninth_templates_and_extended_template_exclusion(self):
        self.assertEqual(name_chord([62, 65, 69, 72, 76]), ("Dm9", 1.0))
        # Complete C11 is scored as C9 with one extra; C11 is excluded.
        self.assertEqual(name_chord([48, 52, 55, 58, 62, 65]), ("C9", 0.9))

    def test_to_roman(self):
        for symbol, key, expected in [
            ("Bb", Key(0, "major"), "bVII"),
            ("Dm7", Key(0, "major"), "ii7"),
            ("A7", Key(2, "minor"), "V7"),
            ("Dm9", Key(2, "minor"), "i9"),
            ("G/B", Key(0, "major"), "V/B"),
            ("Bdim7", Key(0, "major"), "viidim7"),
            ("F#m7b5", Key(0, "major"), "#iv7b5"),
            ("Bbmaj7", Key(2, "minor"), "VImaj7"),
            ("CmMaj7", Key(0, "major"), "iMaj7"),
            ("?", Key(0, "major"), "?"),
        ]:
            with self.subTest(symbol=symbol, key=key):
                self.assertEqual(to_roman(symbol, key), expected)


class DetectionTests(unittest.TestCase):
    def test_detect_roundtrip(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "progression.mid"
            write_smf(_progression("C - G - Am - F"), path)
            spans = detect_chords(read_smf(path), key=Key(0, "major"))
        self.assertEqual([s.symbol.split("/")[0] for s in spans], ["C", "G", "Am", "F"])
        self.assertEqual([s.roman.split("/")[0] for s in spans], ["I", "V", "vi", "IV"])
        self.assertEqual([s.start_beat for s in spans], [0, 4, 8, 12])

    def test_overlap_uses_sustains_and_ten_percent_threshold(self):
        # No new chord note starts in window 2. Two short D events total 10%.
        song = _song(_notes([60, 64, 67], duration=960)
                     + _notes([61], start=480, duration=47)
                     + _notes([62], start=480, duration=24)
                     + _notes([62], start=504, duration=24))
        spans = detect_chords(song, key=Key(0, "major"))
        self.assertEqual([(s.start_beat, s.end_beat, s.symbol) for s in spans],
                         [(0, 1, "C"), (1, 2, "Cadd9")])

    def test_window_boundaries_silence_partial_end_and_ppq(self):
        song = _song(_notes([60, 64, 67], start=96, duration=144)
                     + _notes([65, 69, 72], start=384, duration=144), ppq=96)
        spans = detect_chords(song, window_beats=1, key=Key(0, "major"))
        self.assertEqual([(s.start_beat, s.end_beat, s.symbol) for s in spans],
                         [(0, 1, "?"), (1, 3, "C"), (3, 4, "?"),
                          (4, 5.5, "F")])

    def test_detection_ignores_channel_nine_even_in_mixed_track(self):
        song = _song(_notes([60, 64, 67], duration=960)
                     + _notes(range(35, 60), duration=4800, channel=9))
        spans = detect_chords(song, key=Key(0, "major"))
        self.assertEqual([(s.start_beat, s.end_beat, s.symbol) for s in spans],
                         [(0, 2, "C")])
        self.assertEqual(detect_chords(_song(_notes([36, 42], channel=9))), [])
        self.assertEqual(detect_chords(_song([])), [])

    def test_invalid_windows_rejected(self):
        for window in (0, -1, math.inf, math.nan):
            with self.subTest(window=window), self.assertRaises(ValueError):
                detect_chords(_song([]), window_beats=window)


class AnalyzeCliTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def cli(self, *args):
        # Match make_midi's standalone import behavior from an unrelated cwd.
        return subprocess.run([sys.executable, "-I", str(SCRIPT), *map(str, args)],
                              cwd=self.root, capture_output=True, text=True,
                              encoding="utf-8", env=dict(os.environ, PYTHONIOENCODING="cp1252"))

    def write(self, song, filename="input.mid"):
        path = self.root / filename
        write_smf(song, path)
        return path

    def test_cli_text_and_json(self):
        path = self.write(_progression("Dm - Gm - A7 - Dm", "D minor"))
        text = self.cli(path)
        self.assertEqual(text.returncode, 0, text.stderr)
        self.assertRegex(text.stdout, r"Key: D minor \(-?\d\.\d{2}\) — runner-up: .+ \(-?\d\.\d{2}\)")
        self.assertIn("Bar 1 beat 1: Dm (i)", text.stdout)
        self.assertIn("heuristic", text.stdout.lower())
        result = self.cli(path, "--json")
        self.assertEqual(result.returncode, 0, result.stderr)
        data = json.loads(result.stdout)
        self.assertEqual(data["key"]["name"], "D minor")
        self.assertEqual(data["key"]["tonic"], 2)
        self.assertEqual(data["key"]["mode"], "minor")
        self.assertGreaterEqual(data["key"]["score"], data["runner_up"]["score"])
        self.assertIn("heuristic", data["score_kind"])
        self.assertIn("not", data["score_kind"])
        self.assertEqual([c["symbol"].split("/")[0] for c in data["chords"]],
                         ["Dm", "Gm", "A7", "Dm"])

    def test_cli_ignores_drums_for_key_and_chords(self):
        song = _progression("Dm - Gm - A7 - Dm", "D minor")
        clean = json.loads(self.cli(self.write(song, "clean.mid"), "--json").stdout)
        song.tracks.append(Track("Drums", 9, _notes(range(35, 82), duration=12000, channel=9)))
        mixed = self.cli(self.write(song, "mixed.mid"), "--json")
        self.assertEqual(mixed.returncode, 0, mixed.stderr)
        self.assertEqual(json.loads(mixed.stdout), clean)

    def test_cli_track_filter_controls_both_analyses_and_unicode_paths(self):
        piano = _progression("Dm - Gm - A7 - Dm", "D minor").tracks[0]
        other = Track("Other", 1, _notes([60, 64, 67], duration=20000, channel=1))
        path = self.write(Song(120, (4, 4), [piano, other]), "เพลง ใหม่.mid")
        result = self.cli(path, "--track", "Harmony", "--json")
        self.assertEqual(result.returncode, 0, result.stderr)
        data = json.loads(result.stdout)
        self.assertEqual(data["key"]["name"], "D minor")
        self.assertEqual(len(data["chords"]), 4)
        other_result = self.cli(path, "--track", "Other", "--json")
        self.assertEqual(other_result.returncode, 0, other_result.stderr)
        self.assertEqual(json.loads(other_result.stdout)["chords"][0]["symbol"], "C")
        missing = self.cli(path, "--track", "Missing")
        self.assertEqual(missing.returncode, 2, missing.stderr)
        self.assertIn("Missing", missing.stderr)

    def test_cli_supplied_window_and_key(self):
        path = self.write(_song(_notes([60, 64, 67], duration=240)
                                + _notes([65, 69, 72], start=240, duration=240)))
        result = self.cli(path, "--window", "0.5", "--key", "G major", "--json")
        self.assertEqual(result.returncode, 0, result.stderr)
        data = json.loads(result.stdout)
        self.assertEqual(data["key"]["name"], "G major")
        self.assertEqual(data["key_source"], "supplied")
        self.assertEqual([(c["start_beat"], c["end_beat"], c["symbol"], c["roman"])
                          for c in data["chords"]], [(0, 0.5, "C", "IV"), (0.5, 1, "F", "bVII")])

    def test_cli_compound_meter_bar_and_beat_labels(self):
        path = self.write(_song(_notes([60, 64, 67], duration=1440)
                                + _notes([65, 69, 72], start=1440), signature=(6, 8)))
        result = self.cli(path, "--key", "C major")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Bar 2 beat 1: F (IV)", result.stdout)

    def test_cli_drums_only_and_empty_files_have_no_key(self):
        for notes in ([], _notes([36, 42], channel=9)):
            with self.subTest(notes=notes):
                path = self.write(_song(notes))
                result = self.cli(path, "--json")
                self.assertEqual(result.returncode, 0, result.stderr)
                data = json.loads(result.stdout)
                self.assertIsNone(data["key"])
                self.assertIsNone(data["runner_up"])
                self.assertEqual(data["chords"], [])
                self.assertIn("Key: unknown", self.cli(path).stdout)

    def test_cli_bad_and_unreadable_file_exit2(self):
        bad = self.root / "broken.mid"
        bad.write_bytes(b"not MIDI")
        truncated = self.root / "truncated.mid"
        truncated.write_bytes(b"MThd\x00\x00\x00\x06\x00")
        for path in (bad, truncated, self.root / "missing.mid", self.root):
            with self.subTest(path=path):
                result = self.cli(path, "--json")
                self.assertEqual(result.returncode, 2, result.stderr)
                self.assertEqual(result.stdout, "")
                self.assertIn("error:", result.stderr)
                self.assertNotIn("Traceback", result.stderr)

    def test_cli_invalid_options_exit2(self):
        path = self.write(_song(_notes([60, 64, 67])))
        for options in (("--window", "0"), ("--window", "-1"),
                        ("--window", "nan"), ("--window", "inf"),
                        ("--window", "oops"), ("--key", "H minor")):
            with self.subTest(options=options):
                result = self.cli(path, *options)
                self.assertEqual(result.returncode, 2, result.stderr)
                self.assertEqual(result.stdout, "")
                self.assertNotIn("Traceback", result.stderr)

    def test_cli_malformed_smf_structure_exit2(self):
        path = self.write(_song(_notes([60, 64, 67])))
        valid = path.read_bytes()
        missing_tracks = b"MThd" + struct.pack(">IHHH", 6, 1, 1, 480)
        for data in (missing_tracks, valid[:10] + b"\x00\x03" + valid[12:],
                     valid + b"MTr", valid[:12] + b"\x00\x00" + valid[14:]):
            with self.subTest(data=data):
                path.write_bytes(data)
                result = self.cli(path)
                self.assertEqual(result.returncode, 2, result.stderr)
                self.assertNotIn("Traceback", result.stderr)

    def test_cli_invalid_midi_event_bytes_exit2(self):
        path = self.root / "invalid-event.mid"
        for event in (b"\x00\x90\x80\x64", b"\x00\x90\x3c\x80",
                      b"\x00\xf1\x3c\x64"):
            with self.subTest(event=event):
                body = event + b"\x00\xff\x2f\x00"
                path.write_bytes(b"MThd" + struct.pack(">IHHH", 6, 0, 1, 480)
                                 + b"MTrk" + struct.pack(">I", len(body)) + body)
                result = self.cli(path)
                self.assertEqual(result.returncode, 2, result.stderr)
                self.assertNotIn("Traceback", result.stderr)


if __name__ == "__main__":
    unittest.main()
