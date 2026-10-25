from __future__ import annotations

import struct
import tempfile
import unittest
from pathlib import Path

from scmidi.model import MidiError, Note, Song, Track
from scmidi.midi_reader import decode_smf, read_smf
from scmidi.midi_writer import encode_smf, write_smf


def _vlq(value: int) -> bytes:
    out = [value & 0x7F]
    value >>= 7
    while value:
        out.append((value & 0x7F) | 0x80)
        value >>= 7
    return bytes(reversed(out))


def _smf(fmt: int, tracks: list[bytes], ppq: int = 480) -> bytes:
    data = b"MThd" + struct.pack(">IHHH", 6, fmt, len(tracks), ppq)
    for body in tracks:
        data += b"MTrk" + struct.pack(">I", len(body)) + body
    return data


def _sorted(notes):
    return sorted(notes, key=lambda n: (n.start, n.pitch, n.duration))


class MidiIoTest(unittest.TestCase):
    def _song(self, notes=None, bpm=120.0, ts=(4, 4), ntracks=1):
        if notes is None:
            notes = [Note(60, 0, 480, 100, 0)]
        tracks = [Track(f"T{i}", 0, list(notes)) for i in range(ntracks)]
        return Song(bpm=bpm, time_signature=ts, tracks=tracks)

    def test_roundtrip_notes_tempo_timesig(self):
        notes = [
            Note(60, 0, 480, 100, 0),
            Note(64, 480, 240, 90, 0),
            Note(67, 720, 960, 80, 0),
        ]
        song = Song(bpm=90, time_signature=(3, 4), tracks=[Track("Piano", 0, notes)])
        back = decode_smf(encode_smf(song))
        self.assertAlmostEqual(back.bpm, 90.0, delta=0.01)
        self.assertEqual(back.time_signature, (3, 4))
        self.assertEqual(back.ppq, 480)
        self.assertEqual(len(back.tracks), 1)
        self.assertEqual(back.tracks[0].name, "Piano")
        self.assertEqual(back.tracks[0].channel, 0)
        self.assertEqual(_sorted(back.tracks[0].notes), _sorted(notes))

    def test_header_is_type1_ppq480(self):
        data = encode_smf(self._song())
        self.assertTrue(data.startswith(b"MThd\x00\x00\x00\x06\x00\x01"))
        self.assertEqual(data[12:14], b"\x01\xe0")

    def test_track0_is_conductor(self):
        data = encode_smf(self._song(ntracks=2))
        ntrks = struct.unpack(">H", data[10:12])[0]
        self.assertEqual(ntrks, 3)

    def test_invalid_velocity_raises(self):
        with self.assertRaises(MidiError):
            encode_smf(self._song([Note(60, 0, 480, 0, 0)]))
        with self.assertRaises(MidiError):
            encode_smf(self._song([Note(128, 0, 480, 100, 0)]))

    def test_invalid_start_and_duration_raise(self):
        with self.assertRaises(MidiError):
            encode_smf(self._song([Note(60, -1, 480, 100, 0)]))
        with self.assertRaises(MidiError):
            encode_smf(self._song([Note(60, 0, 0, 100, 0)]))

    def test_invalid_song_writes_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sub" / "bad.mid"
            with self.assertRaises(MidiError):
                write_smf(self._song([Note(60, 0, 480, 0, 0)]), path)
            self.assertFalse(path.exists())

    def test_reads_type0_running_status_vel0_off(self):
        body = (
            # tempo 500000 (120 bpm)
            b"\x00\xff\x51\x03\x07\xa1\x20"
            # ch0 note-on 60 vel 100, then running-status note-on 64 vel 90
            + b"\x00\x90\x3c\x64"
            + b"\x00\x40\x5a"
            # ch9 note-on 36 vel 110
            + b"\x00\x99\x24\x6e"
            # tick 240: ch9 vel-0 off for 36 (explicit status)
            + _vlq(240) + b"\x99\x24\x00"
            # tick 480: ch0 vel-0 off for 60, running status off for 64
            + _vlq(240) + b"\x90\x3c\x00"
            + b"\x00\x40\x00"
            + b"\x00\xff\x2f\x00"
        )
        song = decode_smf(_smf(0, [body]))
        self.assertAlmostEqual(song.bpm, 120.0, delta=0.01)
        self.assertEqual(len(song.tracks), 2)
        by_ch = {t.channel: t for t in song.tracks}
        self.assertEqual(set(by_ch), {0, 9})
        self.assertEqual(
            _sorted(by_ch[0].notes),
            [Note(60, 0, 480, 100, 0), Note(64, 0, 480, 90, 0)],
        )
        self.assertEqual(by_ch[9].notes, [Note(36, 0, 240, 110, 9)])

    def test_missing_tempo_defaults_120(self):
        body = b"\x00\x90\x3c\x64" + _vlq(480) + b"\x80\x3c\x40" + b"\x00\xff\x2f\x00"
        song = decode_smf(_smf(0, [body]))
        self.assertEqual(song.bpm, 120.0)
        self.assertEqual(song.time_signature, (4, 4))
        self.assertEqual(song.tracks[0].notes, [Note(60, 0, 480, 100, 0)])

    def test_first_tempo_wins(self):
        body = (
            b"\x00\xff\x51\x03" + (1_000_000).to_bytes(3, "big")
            + b"\x00\x90\x3c\x64" + _vlq(480) + b"\x80\x3c\x40"
            + b"\x00\xff\x51\x03" + (500_000).to_bytes(3, "big")
            + b"\x00\xff\x2f\x00"
        )
        self.assertAlmostEqual(decode_smf(_smf(0, [body])).bpm, 60.0, delta=0.01)

    def test_overlapping_same_pitch(self):
        body = (
            b"\x00\x90\x3c\x64"
            + _vlq(100) + b"\x90\x3c\x50"
            + _vlq(100) + b"\x80\x3c\x40"
            + _vlq(100) + b"\x80\x3c\x40"
            + b"\x00\xff\x2f\x00"
        )
        notes = decode_smf(_smf(0, [body])).tracks[0].notes
        self.assertEqual(
            _sorted(notes),
            [Note(60, 0, 200, 100, 0), Note(60, 100, 200, 80, 0)],
        )

    def test_unmatched_note_on_ends_at_track_end(self):
        body = b"\x00\x90\x3c\x64" + _vlq(960) + b"\xff\x2f\x00"
        notes = decode_smf(_smf(0, [body])).tracks[0].notes
        self.assertEqual(notes, [Note(60, 0, 960, 100, 0)])

    def test_unicode_path_with_spaces(self):
        song = self._song([Note(62, 0, 240, 77, 0)])
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "โฟลเดอร์ เพลง" / "ไฟล์ ทดสอบ.mid"
            write_smf(song, path)
            self.assertTrue(path.exists())
            back = read_smf(path)
            self.assertEqual(back.tracks[0].notes, [Note(62, 0, 240, 77, 0)])


if __name__ == "__main__":
    unittest.main()
