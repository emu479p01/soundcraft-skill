"""Encode a Song as a type 1 Standard MIDI File (track 0 = conductor)."""
from __future__ import annotations

import struct
from pathlib import Path

from .model import Song, validate_song


def _vlq(value: int) -> bytes:
    out = [value & 0x7F]
    value >>= 7
    while value:
        out.append((value & 0x7F) | 0x80)
        value >>= 7
    return bytes(reversed(out))


def _chunk(kind: bytes, body: bytes) -> bytes:
    return kind + struct.pack(">I", len(body)) + body


def _track(events: list[tuple[int, int, bytes]], end_tick: int) -> bytes:
    """events are (tick, order, raw bytes); lower order sorts first at equal ticks."""
    body = bytearray()
    now = 0
    for tick, _order, raw in sorted(events, key=lambda e: (e[0], e[1])):
        body += _vlq(tick - now) + raw
        now = tick
    body += _vlq(max(end_tick, now) - now) + b"\xff\x2f\x00"
    return _chunk(b"MTrk", bytes(body))


def _conductor(song: Song) -> bytes:
    tempo = round(60_000_000 / song.bpm)
    num, den = song.time_signature
    events = [
        (0, 0, b"\xff\x51\x03" + tempo.to_bytes(3, "big")),
        (0, 1, bytes([0xFF, 0x58, 0x04, num, den.bit_length() - 1, 24, 8])),
    ]
    return _track(events, 0)


def encode_smf(song: Song) -> bytes:
    """Return SMF bytes for the song. Raises MidiError on invalid data."""
    validate_song(song)
    chunks = [_conductor(song)]
    for track in song.tracks:
        name = track.name.encode("utf-8")
        events: list[tuple[int, int, bytes]] = [(0, -1, b"\xff\x03" + _vlq(len(name)) + name)]
        end_tick = 0
        for note in track.notes:
            end = note.start + note.duration
            end_tick = max(end_tick, end)
            # order 0 = note-off, 1 = note-on: offs come before ons at equal ticks
            events.append((note.start, 1, bytes([0x90 | note.channel, note.pitch, note.velocity])))
            events.append((end, 0, bytes([0x80 | note.channel, note.pitch, 0x40])))
        chunks.append(_track(events, end_tick))
    header = _chunk(b"MThd", struct.pack(">HHH", 1, len(chunks), song.ppq))
    return header + b"".join(chunks)


def write_smf(song: Song, path: str | Path) -> None:
    """Validate and encode the song, then write it, creating parent dirs."""
    data = encode_smf(song)  # raises before anything touches the filesystem
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)
