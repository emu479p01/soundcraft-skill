#!/usr/bin/env python3
"""Analyze MIDI keys and chords. Uses only Python 3.9+ standard library modules.

Usage: python analyze_midi.py FILE.mid [--window BEATS] [--track NAME]
                              [--key "D minor"] [--json]
Exit codes: 0 success, 2 unreadable/invalid MIDI or invalid analysis options,
1 unexpected error. Channel 9 is excluded from all key and chord analysis.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).resolve().parent))

from scmidi.analysis import detect_chords, estimate_key  # noqa: E402
from scmidi.midi_reader import read_smf  # noqa: E402
from scmidi.model import Song, Track, validate_song  # noqa: E402
from scmidi.theory import parse_key  # noqa: E402


SCORE_KIND = "Pearson correlation: heuristic, not a calibrated probability"


def _utf8_streams() -> None:
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            try:
                reconfigure(encoding="utf-8")
            except (ValueError, OSError):
                pass


def _key_data(guess) -> dict:
    return {"name": guess.key.name, "tonic": guess.key.tonic,
            "mode": guess.key.mode, "score": guess.score}


def main(argv: Optional[list[str]] = None) -> int:
    _utf8_streams()
    parser = argparse.ArgumentParser(description="Estimate MIDI keys and chords; ignore channel 9 drums.")
    parser.add_argument("file", help="Standard MIDI File to analyze")
    parser.add_argument("--window", type=float, default=1.0, help="chord window in quarter-note beats (default: 1)")
    parser.add_argument("--track", help="analyze only tracks matching this exact name")
    parser.add_argument("--key", help="use this key for Roman numerals, e.g. D minor")
    parser.add_argument("--json", action="store_true", help="print analysis as JSON")
    args = parser.parse_args(argv)
    try:
        if not math.isfinite(args.window) or args.window <= 0:
            raise ValueError("--window must be a finite number greater than zero")
        supplied_key = parse_key(args.key) if args.key is not None else None
        original = read_smf(args.file)
        tracks = original.tracks
        if args.track is not None:
            tracks = [track for track in tracks if track.name == args.track]
            if not tracks:
                raise ValueError(f"--track {args.track!r}: no matching track in MIDI file")
        # Decode the entire file first; only contributing notes need to be writable.
        tracks = [Track(t.name, t.channel, [n for n in t.notes
                                          if n.channel != 9 and n.duration != 0]) for t in tracks]
        song = Song(original.bpm, original.time_signature, tracks, original.ppq)
        validate_song(song)
        notes = [n for track in tracks for n in track.notes]
        guesses = estimate_key(notes) if notes else []
        selected = next((g for g in guesses if g.key == supplied_key), None) if supplied_key else (
            guesses[0] if guesses else None)
        runner_up = next((g for g in guesses if g.key != selected.key), None) if selected else None
        key = supplied_key or (selected.key if selected else None)
        spans = detect_chords(song, args.window, key)
    except (OSError, ValueError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    except Exception as e:  # noqa: BLE001 - report, never a traceback
        print(f"error: unexpected {type(e).__name__}: {e}", file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps({"key": _key_data(selected) if selected else None,
                          "runner_up": _key_data(runner_up) if runner_up else None,
                          "key_source": "supplied" if supplied_key else "estimated",
                          "score_kind": SCORE_KIND,
                          "chords": [asdict(span) for span in spans]}, indent=2))
    else:
        if selected:
            print(f"Key: {selected.key.name} ({selected.score:.2f}) — "
                  f"runner-up: {runner_up.key.name} ({runner_up.score:.2f})")
        else:
            print("Key: unknown (no pitched notes)")
        print(f"Scores: {SCORE_KIND}.")
        beats_per_bar = song.time_signature[0] * 4 / song.time_signature[1]
        for span in spans:
            bar = math.floor(span.start_beat / beats_per_bar)
            beat = (span.start_beat - bar * beats_per_bar) * song.time_signature[1] / 4 + 1
            print(f"Bar {bar + 1} beat {beat:g}: {span.symbol} ({span.roman})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
