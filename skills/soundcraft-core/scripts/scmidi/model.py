"""Data model shared by the MIDI writer and reader. All times are in ticks."""
from __future__ import annotations

from dataclasses import dataclass, field


class MidiError(ValueError):
    """Raised for invalid song data or malformed MIDI files."""


@dataclass(frozen=True)
class Note:
    pitch: int
    start: int
    duration: int
    velocity: int
    channel: int


@dataclass
class Track:
    name: str
    channel: int
    notes: list[Note] = field(default_factory=list)


@dataclass
class Song:
    bpm: float
    time_signature: tuple[int, int]
    tracks: list[Track]
    ppq: int = 480


def _is_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def validate_note(note: Note) -> None:
    """Raise MidiError unless the note is writable."""
    if not _is_int(note.pitch) or not 0 <= note.pitch <= 127:
        raise MidiError(f"pitch must be 0-127, got {note.pitch!r} in {note}")
    if not _is_int(note.velocity) or not 1 <= note.velocity <= 127:
        raise MidiError(f"velocity must be 1-127, got {note.velocity!r} in {note}")
    if not _is_int(note.start) or note.start < 0:
        raise MidiError(f"start must be >= 0, got {note.start!r} in {note}")
    if not _is_int(note.duration) or note.duration <= 0:
        raise MidiError(f"duration must be > 0, got {note.duration!r} in {note}")
    if not _is_int(note.channel) or not 0 <= note.channel <= 15:
        raise MidiError(f"channel must be 0-15, got {note.channel!r} in {note}")


def validate_song(song: Song) -> None:
    """Raise MidiError unless the whole song is writable."""
    if not _is_int(song.ppq) or not 1 <= song.ppq <= 0x7FFF:
        raise MidiError(f"ppq must be 1-32767, got {song.ppq!r}")
    if isinstance(song.bpm, bool) or not isinstance(song.bpm, (int, float)):
        raise MidiError(f"bpm must be a number, got {song.bpm!r}")
    if not song.bpm > 0 or not 1 <= round(60_000_000 / song.bpm) <= 0xFFFFFF:
        raise MidiError(f"bpm out of range: {song.bpm!r}")
    try:
        num, den = song.time_signature
    except (TypeError, ValueError):
        raise MidiError(
            f"time_signature must be (numerator, denominator), got {song.time_signature!r}"
        ) from None
    if not _is_int(num) or not 1 <= num <= 255:
        raise MidiError(f"time signature numerator must be 1-255, got {num!r}")
    if not _is_int(den) or den < 1 or den & (den - 1) or den.bit_length() - 1 > 255:
        raise MidiError(f"time signature denominator must be a power of two, got {den!r}")
    for track in song.tracks:
        if not _is_int(track.channel) or not 0 <= track.channel <= 15:
            raise MidiError(f"track channel must be 0-15, got {track.channel!r}")
        for note in track.notes:
            validate_note(note)
