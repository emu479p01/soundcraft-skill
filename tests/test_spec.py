from __future__ import annotations

import json
import unittest
from pathlib import Path

from scmidi.midi_writer import encode_smf
from scmidi.render import render
from scmidi.spec import SpecError, validate_spec

EXAMPLE = (Path(__file__).resolve().parent.parent / "skills" / "soundcraft-core"
           / "examples" / "lofi-sketch.json")
BAR = 1920  # 4/4 at PPQ 480


def _run(raw: dict):
    return render(validate_spec(raw))


def _chords(**fields) -> dict:
    track = {"type": "chords", "progression": ["C"]}
    track.update(fields)
    return track


def _drums(**fields) -> dict:
    track = {"type": "drums", "pattern": {"kick": "x...x...x...x..."}}
    track.update(fields)
    return track


class SpecTests(unittest.TestCase):
    def assertSpecError(self, raw: dict, path: str, *fragments: str) -> SpecError:
        with self.assertRaises(SpecError) as cm:
            _run(raw)
        self.assertEqual(cm.exception.path, path, str(cm.exception))
        for fragment in fragments:
            self.assertIn(fragment, cm.exception.message)
        self.assertEqual(str(cm.exception), f"{path}: {cm.exception.message}")
        return cm.exception

    def test_example_spec_validates_and_renders(self):
        raw = json.loads(EXAMPLE.read_text(encoding="utf-8"))
        song, lines = _run(raw)
        self.assertEqual(len(song.tracks), 2)
        data = encode_smf(song)
        self.assertEqual(data.count(b"MTrk"), 3)  # conductor + 2 tracks
        self.assertTrue(lines[0].startswith("Bar 1: Dm9 = "), lines[0])
        self.assertEqual(song.bpm, 90)

    def test_defaults_applied(self):
        raw = {"tracks": [{"type": "chords", "progression": "C - G - Am - F"}]}
        spec = validate_spec(raw)
        self.assertEqual(spec["bpm"], 120)
        self.assertEqual(spec["time_signature"], [4, 4])
        self.assertEqual(spec["output"], "out.mid")
        self.assertEqual(spec["tracks"][0]["voicing"], "close")
        self.assertEqual(len(spec["tracks"][0]["progression"]), 4)
        song, lines = render(spec)
        self.assertEqual(song.bpm, 120)
        self.assertEqual(len(lines), 4)
        notes = song.tracks[0].notes
        self.assertEqual(len({n.start for n in notes}), 4)
        self.assertEqual(max(n.start + n.duration for n in notes), 4 * BAR)
        self.assertTrue(all(n.velocity == 90 for n in notes))

    def test_input_not_mutated(self):
        raw = {"tracks": [{"type": "chords", "progression": "C - G"}]}
        validate_spec(raw)
        self.assertEqual(raw, {"tracks": [{"type": "chords", "progression": "C - G"}]})

    def test_unknown_field_suggestion(self):
        self.assertSpecError({"tracks": [_chords(voiceing="open")]},
                             "tracks[0].voiceing", "did you mean 'voicing'")
        self.assertSpecError({"bmp": 90, "tracks": [_chords()]}, "bmp",
                             "did you mean 'bpm'")
        self.assertSpecError({"tracks": [_drums(fill={"evry": 2, "pattern": {}})]},
                             "tracks[0].fill.evry", "did you mean 'every'")

    def test_bad_chord_path(self):
        err = self.assertSpecError({"tracks": [_chords(progression=["C", "Xm7"])]},
                                   "tracks[0].progression[1]")
        self.assertIn("'X' is not a note name", err.message)  # original text kept

    def test_roman_requires_key(self):
        self.assertSpecError({"tracks": [_chords(progression="i - VI")]},
                             "tracks[0].progression[0]", "key")

    def test_roman_with_key_renders(self):
        song, lines = _run({"key": "D minor", "tracks": [_chords(progression="i - VI")]})
        self.assertIn("Dm", lines[0])
        self.assertIn("Bb", lines[1])

    def test_range_too_narrow(self):
        self.assertSpecError({"tracks": [_chords(range=[60, 65])]}, "tracks[0].range")

    def test_bad_values_name_accepted(self):
        self.assertSpecError({"bpm": 400, "tracks": [_chords()]}, "bpm", "400", "20")
        self.assertSpecError({"tracks": [_chords(voicing="wide")]},
                             "tracks[0].voicing", "'wide'", "drop2")
        self.assertSpecError({"tracks": [_chords(rhythm="swingy")]},
                             "tracks[0].rhythm", "arp-up")
        self.assertSpecError({"tracks": [_chords(octave=True)]}, "tracks[0].octave")
        self.assertSpecError({"time_signature": [4, 3], "tracks": [_chords()]},
                             "time_signature", "16")
        self.assertSpecError({"key": "H major", "tracks": [_chords()]}, "key", "'H'")
        self.assertSpecError({"tracks": []}, "tracks")
        self.assertSpecError({"tracks": [{"type": "bass"}]}, "tracks[0].type",
                             "chords", "drums")
        self.assertSpecError({"tracks": [_drums(steps=10)]}, "tracks[0].steps", "16")
        self.assertSpecError({"tracks": [_drums(pattern={"kik": "x..."})]},
                             "tracks[0].pattern.kik", "did you mean 'kick'")
        self.assertSpecError({"tracks": [_drums(pattern={"kick": "x.."})]},
                             "tracks[0].pattern.kick", "multiple of 16")

    def test_custom_rhythm_needs_16_steps(self):
        self.assertSpecError({"tracks": [_chords(rhythm="custom")]}, "tracks[0].steps")
        self.assertSpecError({"tracks": [_chords(rhythm="custom", steps="x...x...")]},
                             "tracks[0].steps", "16")
        self.assertSpecError({"tracks": [_chords(rhythm="pad", steps="x" * 16)]},
                             "tracks[0].steps", "custom")
        song, _ = _run({"tracks": [_chords(rhythm="custom", steps="x...x...x...x...")]})
        self.assertEqual(sorted({n.start for n in song.tracks[0].notes}),
                         [0, 480, 960, 1440])

    def test_arp_uses_note_count(self):
        song, _ = _run({"tracks": [_chords(rhythm="arp-up", bass_note=True)]})
        notes = song.tracks[0].notes
        self.assertEqual(len(notes), 16)
        self.assertEqual(len({n.pitch for n in notes[:4]}), 4)  # bass + C E G

    def test_bass_note_in_notes_and_summary(self):
        song, lines = _run({"tracks": [_chords(progression=["G/B"])]})
        pitches = sorted(n.pitch for n in song.tracks[0].notes)
        self.assertEqual(pitches[0] % 12, 11)
        self.assertEqual(len(pitches), 4)
        self.assertEqual(lines[0].split(" = ")[1].split()[0][0], "B")

    def test_drum_fill_every_4(self):
        raw = {"tracks": [_drums(
            bars=8,
            pattern={"kick": "x...x...x...x...", "snare": "....x.......x..."},
            fill={"every": 4, "pattern": {"snare": "x.x.x.x.x.x.x.x."}})]}
        song, lines = _run(raw)
        notes = song.tracks[0].notes

        def in_bar(pitch, bar):
            return [n.start - bar * BAR for n in notes
                    if n.pitch == pitch and bar * BAR <= n.start < (bar + 1) * BAR]

        for bar in (3, 7):
            self.assertEqual(len(in_bar(38, bar)), 8)
            self.assertEqual(in_bar(36, bar), [0, 480, 960, 1440])
        for bar in (0, 1, 2, 4, 5, 6):
            self.assertEqual(in_bar(38, bar), [480, 1440])
        self.assertEqual(len(lines), 8)
        self.assertEqual(lines[3], "Bar 4: kick×4 snare×8")
        self.assertEqual(lines[0], "Bar 1: kick×4 snare×2")

    def test_multi_bar_voice_cycles(self):
        song, _ = _run({"tracks": [_drums(bars=4, pattern={
            "kick": "x...............|x...x..........."})]})
        starts = [n.start for n in song.tracks[0].notes]
        self.assertEqual(starts, [0, BAR, BAR + 480, 2 * BAR, 3 * BAR, 3 * BAR + 480])

    def test_offset_and_velocity_overrides(self):
        raw = {"bpm": 120, "tracks": [_drums(
            bars=1,
            pattern={"snare": "....x...........", "hat": "x.x.x.x.x.x.x.x."},
            offset_ms={"snare": 25}, velocity={"hat": {"x": 85}})]}
        song, _ = _run(raw)
        notes = song.tracks[0].notes
        self.assertEqual([n.start for n in notes if n.pitch == 38], [480 + 24])
        self.assertEqual({n.velocity for n in notes if n.pitch == 42}, {85})
        self.assertEqual({n.duration for n in notes}, {120})

    def test_negative_offset_clamps(self):
        song, _ = _run({"tracks": [_drums(bars=1, offset_ms={"kick": -50})]})
        self.assertEqual(min(n.start for n in song.tracks[0].notes), 0)

    def test_soundcraft_unsupported_voice(self):
        self.assertSpecError(
            {"tracks": [_drums(drum_map="soundcraft", pattern={"rim": "x" * 16})]},
            "tracks[0].pattern.rim", "voice 'rim' is not available in drum_synth",
            "37 plays a clap", 'use drum_map "gm"')
        self.assertSpecError(
            {"tracks": [_drums(drum_map="soundcraft",
                               fill={"every": 2, "pattern": {"cowbell": "x" * 16}})]},
            "tracks[0].fill.pattern.cowbell", "drum_synth")
        song, _ = _run({"tracks": [_drums(drum_map="soundcraft")]})
        self.assertEqual({n.pitch for n in song.tracks[0].notes}, {36})

    def test_custom_drum_map(self):
        song, _ = _run({"tracks": [_drums(drum_map={"kick": 35})]})
        self.assertEqual({n.pitch for n in song.tracks[0].notes}, {35})
        self.assertSpecError({"tracks": [_drums(drum_map={"kick": 300})]},
                             "tracks[0].drum_map")

    def test_chord_lengths(self):
        song, _ = _run({"tracks": [_chords(
            progression=[{"chord": "G/B", "beats": 2}, "C", {"chord": "F", "bars": 1}],
            chord_length="2bars")]})
        notes = song.tracks[0].notes
        self.assertEqual({n.duration for n in notes if n.start == 0}, {960})
        self.assertEqual({n.duration for n in notes if n.start == 960}, {3840})
        self.assertEqual({n.duration for n in notes if n.start == 4800}, {BAR})
        song, _ = _run({"tracks": [_chords(chord_length=3)]})
        self.assertEqual({n.duration for n in song.tracks[0].notes}, {1440})
        self.assertSpecError({"tracks": [_chords(chord_length="2 weeks")]},
                             "tracks[0].chord_length", "1bar")

    def test_repeat_and_summary_bars(self):
        song, lines = _run({"tracks": [_chords(progression="C | G", repeat=2)]})
        self.assertEqual([l.split(":")[0] for l in lines],
                         ["Bar 1", "Bar 2", "Bar 3", "Bar 4"])

    def test_strum(self):
        song, _ = _run({"tracks": [_chords(progression=["Cmaj7"], strum_ms=15)]})
        notes = sorted(song.tracks[0].notes, key=lambda n: n.pitch)
        starts = [n.start for n in notes]
        self.assertEqual(starts, sorted(set(starts)))
        self.assertTrue(all(n.start + n.duration == BAR for n in notes))

    def test_channels(self):
        song, _ = _run({"tracks": [_chords(), _chords(), _drums()]})
        self.assertEqual([t.channel for t in song.tracks], [0, 1, 9])
        for track in song.tracks:
            self.assertTrue(all(n.channel == track.channel for n in track.notes))
        song, _ = _run({"tracks": [_chords() for _ in range(10)]})
        self.assertEqual([t.channel for t in song.tracks][-2:], [8, 10])
        self.assertSpecError({"tracks": [_chords() for _ in range(16)]}, "tracks")

    def test_out_of_range_note_rejected(self):
        self.assertSpecError({"tracks": [_chords(range=[0, 12], octave=1,
                                                 bass_note=True)]}, "tracks[0]")


if __name__ == "__main__":
    unittest.main()
