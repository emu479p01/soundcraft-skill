"""Heuristic key and chord analysis of MIDI notes (times are in ticks).

Key scores are Pearson correlations, not calibrated probabilities. Chord
scores describe template fit; neither measure establishes musical intent.
"""
from __future__ import annotations

import math
import re
from collections import defaultdict
from dataclasses import dataclass
from typing import Optional

from .model import Note, Song
from .theory import QUALITIES, Key, parse_chord


_PROFILES = {
    "major": (6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88),
    "minor": (6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17),
}
_PC_NAMES = ("C", "Db", "D", "Eb", "E", "F", "F#", "G", "Ab", "A", "Bb", "B")
_SCALES = {"major": (0, 2, 4, 5, 7, 9, 11), "minor": (0, 2, 3, 5, 7, 8, 10)}
_NUMERALS = ("I", "II", "III", "IV", "V", "VI", "VII")


@dataclass
class KeyGuess:
    key: Key
    score: float


def estimate_key(notes: list[Note]) -> list[KeyGuess]:
    """Rank all 24 keys by duration-weighted Krumhansl–Kessler correlation.

    Channel 9 and zero-duration notes contribute nothing. Empty or uniform
    pitch-class histograms have undefined correlation, reported as zero for
    every key. Equal scores retain major-before-minor, ascending-tonic order.
    """
    histogram = [0.0] * 12
    for note in notes:
        if note.channel != 9 and note.duration > 0:
            histogram[note.pitch % 12] += note.duration
    mean = sum(histogram) / 12
    centered = [v - mean for v in histogram]
    energy = sum(v * v for v in centered)
    guesses = []
    for mode, profile in _PROFILES.items():
        profile_mean = sum(profile) / 12
        profile_centered = [v - profile_mean for v in profile]
        denominator = math.sqrt(energy * sum(v * v for v in profile_centered))
        for tonic in range(12):
            numerator = sum(centered[pc] * profile_centered[(pc - tonic) % 12]
                            for pc in range(12))
            score = max(-1.0, min(1.0, numerator / denominator)) if denominator else 0.0
            guesses.append(KeyGuess(Key(tonic, mode), score))
    return sorted(guesses, key=lambda guess: guess.score, reverse=True)


def name_chord(pitches: list[int]) -> tuple[str, float]:
    """Match distinct pitch classes to triad, seventh and ninth templates.

    Ties prefer the root whose actual pitch occurs lowest, then fewer template
    tones, then QUALITIES order. The bass may be a chord tone or an extra.
    """
    pcs = {p % 12 for p in pitches}
    if len(pcs) < 2:
        return "?", 0.0
    lowest = {pc: min(p for p in pitches if p % 12 == pc) for pc in pcs}
    best_rank = None
    best = ("?", 0.0)
    bass = min(pitches) % 12
    for root in sorted(pcs, key=lowest.get):
        for quality, intervals in QUALITIES.items():
            if quality in {"11", "m11", "13", "maj13"}:
                continue
            template = {(root + interval) % 12 for interval in intervals}
            matched = len(pcs & template)
            extra = len(pcs - template)
            missing = len(template - pcs)
            score = (matched - 0.5 * extra - missing) / len(template)
            rank = (score, -lowest[root], -len(template))
            if best_rank is None or rank > best_rank:
                symbol = _PC_NAMES[root] + quality
                if bass != root:
                    symbol += "/" + _PC_NAMES[bass]
                best_rank, best = rank, (symbol, score)
    return best if best[1] >= 0.5 else ("?", best[1])


def to_roman(symbol: str, key: Key) -> str:
    """Express a symbol relative to the key's major or natural minor scale.

    Minor and diminished chords use lowercase numerals; quality extensions
    remain explicit. Slash bass note names are retained. Accidentals on roots
    outside the scale follow their spelling (Bb in C is bVII, F# is #IV).
    """
    if symbol == "?":
        return "?"
    chord = parse_chord(symbol)
    text = re.sub(r"\s+", "", symbol).replace("♯", "#").replace("♭", "b")
    root_match = re.match(r"[A-Ga-g][#b]?", text)
    suffix = text[root_match.end():].split("/")[0]
    quality = next((q for q, intervals in QUALITIES.items()
                    if intervals == chord.intervals), suffix)
    scale = _SCALES[key.mode]
    relative = (chord.root - key.tonic) % 12
    accidental = ""
    if relative in scale:
        degree = scale.index(relative)
    else:
        letters = "CDEFGAB"
        degree = (letters.index(text[0].upper()) - letters.index(key.name[0])) % 7
        shift = (relative - scale[degree] + 6) % 12 - 6
        accidental = "#" * max(0, shift) + "b" * max(0, -shift)
    minor = quality.startswith("m") and not quality.startswith("maj")
    numeral = _NUMERALS[degree].lower() if minor or quality.startswith("dim") else _NUMERALS[degree]
    if minor:
        quality = quality[1:]
    bass = "/" + text.rsplit("/", 1)[1] if chord.bass is not None else ""
    return accidental + numeral + quality + bass


@dataclass
class ChordSpan:
    start_beat: float
    end_beat: float
    symbol: str
    roman: str


def detect_chords(song: Song, window_beats: float = 1.0,
                  key: Optional[Key] = None) -> list[ChordSpan]:
    """Analyze fixed windows and merge adjacent identical symbols.

    Beats are quarter notes. Durations overlapping a window are accumulated
    per MIDI pitch; pitches contributing less than 10% of a full window are
    discarded. Silence is '?'. The final span ends at the last pitched note,
    even when that falls inside a window. Drums never extend the analysis.
    When no key is supplied, use the highest-ranked duration-profile guess.
    """
    if not math.isfinite(window_beats) or window_beats <= 0:
        raise ValueError("window_beats must be a finite number greater than zero")
    if song.ppq <= 0:
        raise ValueError("ppq must be greater than zero")
    window_ticks = window_beats * song.ppq
    if not math.isfinite(window_ticks) or window_ticks <= 0:
        raise ValueError("window_beats produces an invalid tick window")
    notes = sorted((n for t in song.tracks for n in t.notes
                    if n.channel != 9 and n.duration > 0), key=lambda n: n.start)
    if not notes:
        return []
    if key is None:
        key = estimate_key(notes)[0].key
    end_tick = max(n.start + n.duration for n in notes)
    spans: list[ChordSpan] = []
    active: list[Note] = []
    cursor = 0
    index = 0
    while index * window_ticks < end_tick:
        start = index * window_ticks
        end = min((index + 1) * window_ticks, end_tick)
        active = [n for n in active if n.start + n.duration > start]
        while cursor < len(notes) and notes[cursor].start < end:
            note = notes[cursor]
            if note.start + note.duration > start:
                active.append(note)
            cursor += 1
        weights: dict[int, float] = defaultdict(float)
        for note in active:
            weights[note.pitch] += min(end, note.start + note.duration) - max(start, note.start)
        pitches = [pitch for pitch, weight in weights.items() if weight >= window_ticks * 0.1]
        symbol, _ = name_chord(pitches)
        end_beat = end / song.ppq
        if spans and spans[-1].symbol == symbol:
            spans[-1].end_beat = end_beat
        else:
            spans.append(ChordSpan(start / song.ppq, end_beat, symbol, to_roman(symbol, key)))
        index += 1
    return spans
