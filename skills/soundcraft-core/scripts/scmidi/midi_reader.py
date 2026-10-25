"""Decode type 0 / type 1 Standard MIDI Files into a Song."""
from __future__ import annotations

import struct
from collections import deque
from pathlib import Path

from .model import MidiError, Note, Song, Track

DEFAULT_BPM = 120.0
DEFAULT_TIME_SIGNATURE = (4, 4)


class _Cursor:
    def __init__(self, data: bytes) -> None:
        self.data = data
        self.pos = 0

    def byte(self) -> int:
        if self.pos >= len(self.data):
            raise MidiError("unexpected end of track data")
        value = self.data[self.pos]
        self.pos += 1
        return value

    def take(self, count: int) -> bytes:
        if self.pos + count > len(self.data):
            raise MidiError("unexpected end of track data")
        chunk = self.data[self.pos:self.pos + count]
        self.pos += count
        return chunk

    def vlq(self) -> int:
        value = 0
        for _ in range(4):
            b = self.byte()
            value = (value << 7) | (b & 0x7F)
            if not b & 0x80:
                return value
        raise MidiError("variable-length quantity longer than 4 bytes")

    def done(self) -> bool:
        return self.pos >= len(self.data)


def _chunks(data: bytes) -> list[tuple[bytes, bytes]]:
    out = []
    pos = 0
    while pos + 8 <= len(data):
        kind = data[pos:pos + 4]
        (length,) = struct.unpack(">I", data[pos + 4:pos + 8])
        body = data[pos + 8:pos + 8 + length]
        if len(body) != length:
            raise MidiError(f"truncated {kind!r} chunk")
        out.append((kind, body))
        pos += 8 + length
    if pos != len(data):
        raise MidiError("truncated MIDI chunk header")
    return out


class _Globals:
    """Song-wide values; the first occurrence (in file order) wins."""

    def __init__(self) -> None:
        self.bpm: float | None = None
        self.time_signature: tuple[int, int] | None = None


def _parse_track(body: bytes, glob: _Globals) -> tuple[str, dict[int, list[Note]]]:
    """Return (track name, notes per channel) for one MTrk chunk."""
    cur = _Cursor(body)
    name = ""
    tick = 0
    status = 0
    pending: dict[tuple[int, int], deque[tuple[int, int]]] = {}
    notes: dict[int, list[Note]] = {}

    def close(channel: int, pitch: int) -> None:
        queue = pending.get((channel, pitch))
        if queue:
            start, velocity = queue.popleft()  # FIFO pairing of overlapping notes
            notes.setdefault(channel, []).append(
                Note(pitch, start, tick - start, velocity, channel)
            )

    while not cur.done():
        tick += cur.vlq()
        first = cur.byte()
        if first == 0xFF:
            status = 0  # meta events cancel running status
            meta = cur.byte()
            payload = cur.take(cur.vlq())
            if meta == 0x2F:
                break
            if meta == 0x03 and not name:
                name = payload.decode("utf-8", errors="replace")
            elif meta == 0x51 and glob.bpm is None and len(payload) == 3:
                tempo = int.from_bytes(payload, "big")
                if tempo > 0:
                    glob.bpm = 60_000_000 / tempo
            elif meta == 0x58 and glob.time_signature is None and len(payload) >= 2:
                glob.time_signature = (payload[0], 2 ** payload[1])
            continue
        if first in (0xF0, 0xF7):
            status = 0  # sysex cancels running status
            cur.take(cur.vlq())
            continue
        if first & 0x80:
            status = first
            data1 = cur.byte()
        elif status:
            data1 = first  # running status
        else:
            raise MidiError("data byte without a running status")
        kind = status & 0xF0
        channel = status & 0x0F
        if not 0x80 <= status <= 0xEF:
            raise MidiError(f"invalid channel event status 0x{status:02x}")
        if data1 & 0x80:
            raise MidiError("channel event data bytes must be 0-127")
        if kind in (0xC0, 0xD0):
            continue  # one data byte, not note-related
        data2 = cur.byte()
        if data2 & 0x80:
            raise MidiError("channel event data bytes must be 0-127")
        if kind == 0x90 and data2 > 0:
            pending.setdefault((channel, data1), deque()).append((tick, data2))
        elif kind in (0x80, 0x90):  # 0x90 with velocity 0 is a note-off
            close(channel, data1)

    # Unmatched note-ons end at the end of the track.
    for channel, pitch in list(pending):
        while pending[(channel, pitch)]:
            close(channel, pitch)
    return name, notes


def decode_smf(data: bytes) -> Song:
    """Parse SMF bytes (type 0 or 1) into a Song, one Track per (track, channel)."""
    chunks = _chunks(bytes(data))
    if not chunks or chunks[0][0] != b"MThd" or len(chunks[0][1]) < 6:
        raise MidiError("not a Standard MIDI File (missing MThd header)")
    fmt, ntrks, division = struct.unpack(">HHH", chunks[0][1][:6])
    if fmt not in (0, 1):
        raise MidiError(f"unsupported SMF format {fmt}")
    if division & 0x8000:
        raise MidiError("SMPTE time division is not supported")
    if division == 0:
        raise MidiError("PPQ time division must be greater than zero")
    actual_tracks = sum(kind == b"MTrk" for kind, _ in chunks[1:])
    if ntrks == 0 or ntrks != actual_tracks or (fmt == 0 and ntrks != 1):
        raise MidiError(f"invalid track count: format {fmt} declares {ntrks}, found {actual_tracks}")
    glob = _Globals()
    tracks: list[Track] = []
    for kind, body in chunks[1:]:
        if kind != b"MTrk":
            continue  # unknown chunk types are skipped, as the SMF spec requires
        name, by_channel = _parse_track(body, glob)
        for channel in sorted(by_channel):
            notes = sorted(by_channel[channel], key=lambda n: (n.start, n.pitch))
            tracks.append(Track(name, channel, notes))
    return Song(
        bpm=glob.bpm if glob.bpm is not None else DEFAULT_BPM,
        time_signature=glob.time_signature or DEFAULT_TIME_SIGNATURE,
        tracks=tracks,
        ppq=division,
    )


def read_smf(path: str | Path) -> Song:
    """Read and decode an SMF file."""
    return decode_smf(Path(path).read_bytes())
