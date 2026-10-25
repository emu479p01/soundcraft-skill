"""Phrase boundaries are encoded EOT events, independent of reader retention."""
from __future__ import annotations

import struct
import unittest

from scmidi.midi_reader import decode_smf
from scmidi.midi_writer import encode_smf
from scmidi.model import MidiError, Note, Song, Track
from scmidi.render import render
from scmidi.spec import validate_spec


def encoded_end_ticks(data: bytes) -> list[int]:
    """Walk raw SMF events (explicit statuses from our writer), not Song notes."""
    ends = []
    offset = 8 + int.from_bytes(data[4:8], "big")
    while offset < len(data):
        kind, length = struct.unpack_from(">4sI", data, offset)
        assert kind == b"MTrk"
        body = data[offset + 8:offset + 8 + length]
        offset += 8 + length
        pos = 0
        tick = 0

        def vlq():
            nonlocal pos
            value = 0
            while True:
                byte = body[pos]
                pos += 1
                value = (value << 7) | (byte & 127)
                if byte < 128:
                    return value

        while pos < len(body):
            tick += vlq()
            status = body[pos]
            pos += 1
            if status == 0xFF:
                meta = body[pos]
                pos += 1
                size = vlq()
                pos += size
                if meta == 0x2F:
                    assert size == 0 and pos == len(body)
                    ends.append(tick)
                    break
            else:
                assert 0x80 <= status < 0xF0
                pos += 1 if status >> 4 in (0xC, 0xD) else 2
        else:
            raise AssertionError("Missing encoded EOT")
    return ends


class PhraseDurationTests(unittest.TestCase):
    def rendered(self, track, meter=(4, 4)):
        song, _ = render(validate_spec({"time_signature": list(meter), "tracks": [track]}))
        return song, encode_smf(song)

    def test_sparse_four_bar_drums_keep_trailing_rests(self):
        song, data = self.rendered({"type": "drums", "bars": 4,
                                    "pattern": {"kick": "x..............."},
                                    "drum_map": "soundcraft"})
        self.assertEqual(encoded_end_ticks(data), [0, 7680])
        notes = song.tracks[0].notes
        self.assertEqual([n.start for n in notes], [0, 1920, 3840, 5760])
        self.assertEqual([n.duration for n in notes], [120] * 4)
        self.assertEqual(decode_smf(data).tracks[0].notes, notes)

    def test_all_rest_four_bar_chords_keep_empty_phrase(self):
        song, data = self.rendered({"type": "chords", "progression": ["C", "G", "Am", "F"],
                                    "rhythm": "custom", "steps": "." * 16})
        self.assertEqual(encoded_end_ticks(data), [0, 7680])
        self.assertEqual(song.tracks[0].notes, [])

    def test_non_four_four_drum_bar_duration(self):
        for meter, expected in (((3, 4), 5760), ((6, 8), 5760), ((5, 8), 4800)):
            with self.subTest(meter=meter):
                _, data = self.rendered({"type": "drums", "bars": 4,
                                         "pattern": {"kick": "x..............."}}, meter)
                self.assertEqual(encoded_end_ticks(data), [0, expected])

    def test_repeated_chords_use_each_requested_duration(self):
        # One 3/4 bar plus two quarter-note beats, three times: 15 beats.
        _, data = self.rendered({"type": "chords", "progression": [
            {"chord": "C", "bars": 1}, {"chord": "G", "beats": 2}],
            "repeat": 3, "rhythm": "custom", "steps": "." * 16}, (3, 4))
        self.assertEqual(encoded_end_ticks(data), [0, 7200])

    def test_legacy_three_argument_tracks_end_at_last_note_off(self):
        for notes, expected in (([], 0), ([Note(60, 100, 480, 90, 0)], 580)):
            with self.subTest(notes=notes):
                data = encode_smf(Song(120, (4, 4), [Track("Legacy", 0, notes)]))
                self.assertEqual(encoded_end_ticks(data), [0, expected])

    def test_explicit_boundary_never_stretches_or_truncates_notes(self):
        notes = [Note(60, 100, 480, 90, 0)]
        for intended, expected in ((0, 580), (200, 580), (7680, 7680)):
            with self.subTest(intended=intended):
                track = Track("Direct", 0, notes, intended)
                data = encode_smf(Song(120, (4, 4), [track]))
                self.assertEqual(encoded_end_ticks(data), [0, expected])
                self.assertEqual(decode_smf(data).tracks[0].notes, notes)

    def test_late_note_off_is_after_intended_boundary(self):
        notes = [Note(60, 7600, 400, 90, 0)]
        data = encode_smf(Song(120, (4, 4), [Track("Late", 0, notes, 7680)]))
        self.assertEqual(encoded_end_ticks(data), [0, 8000])
        self.assertEqual(decode_smf(data).tracks[0].notes, notes)

    def test_invalid_optional_boundary_is_rejected(self):
        for invalid in (-1, True, False, 1.5, "7680", float("nan")):
            with self.subTest(invalid=invalid):
                track = Track("Invalid", 0, [], invalid)
                with self.assertRaisesRegex(MidiError, "intended_end_tick"):
                    encode_smf(Song(120, (4, 4), [track]))
