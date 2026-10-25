"""Render a validated spec (see spec.validate_spec) to a Song plus a per-bar summary."""
from __future__ import annotations

from typing import Optional

from .drums import VOICES, resolve_drum_map
from .model import MidiError, Note, Song, Track, validate_note
from .rhythm import STEP_VELOCITY, chord_hits, humanize, ms_to_ticks, parse_steps, step_tick
from .spec import CUSTOM_STEPS, PPQ, SpecError
from .theory import Key, TheoryError, parse_chord_token, parse_key, pitch_name, voice_chord

DRUM_CHANNEL = 9


def _chord_track(t: dict, path: str, key: Optional[Key], bpm: float, bpb: float,
                 bar_ticks: int, channel: int) -> tuple[list[Note], list[dict]]:
    custom = parse_steps(t["steps"], CUSTOM_STEPS) if t["rhythm"] == "custom" else None
    strum = ms_to_ticks(t["strum_ms"], bpm, PPQ)
    notes: list[Note] = []
    bars: list[dict] = []
    previous: Optional[list[int]] = None
    start = 0
    for _ in range(t["repeat"]):
        for j, item in enumerate(t["progression"]):
            item_path = f"{path}.progression[{j}]"
            length = round(item["beats"] * PPQ)
            try:
                chord = parse_chord_token(item["chord"], key)
                upper, bass = voice_chord(chord, t["voicing"], t["octave"], tuple(t["range"]),
                                          previous, t["voice_leading"], t["bass_note"])
                pitches = sorted(upper + ([bass] if bass is not None else []))
                hits = chord_hits(t["rhythm"], length, PPQ, bpb, custom, len(pitches))
            except (TheoryError, ValueError) as e:
                raise SpecError(item_path, str(e)) from None
            bar = start // bar_ticks + 1
            low, high = pitches[0], pitches[-1]
            if low < 0 or high > 127:
                raise SpecError(path, f"chord {item['chord']!r} in bar {bar} needs pitch "
                                      f"{low if low < 0 else high}, outside MIDI 0-127; "
                                      f"change 'octave', 'range' or 'bass_note'")
            previous = upper
            for rel, dur, index, scale in hits:
                chosen = pitches if index is None else [pitches[index]]
                velocity = min(127, max(1, round(t["velocity"] * scale)))
                for k, pitch in enumerate(chosen):
                    offset = min(k * strum, dur - 1)  # keep duration >= 1
                    notes.append(Note(pitch, start + rel + offset, dur - offset,
                                      velocity, channel))
            symbol = chord.symbol if item["chord"] == chord.symbol \
                else f"{item['chord']} ({chord.symbol})"
            bars.append({"bar": bar, "chord": symbol,
                         "notes": [pitch_name(p) for p in pitches]})
            start += length
    return humanize(notes, t["humanize"], PPQ, t["seed"]), bars


def _drum_track(t: dict, bpm: float, bpb: float, bar_ticks: int,
                channel: int) -> tuple[list[Note], list[dict]]:
    spb = t["steps"]
    drum_map = resolve_drum_map(t["drum_map"])
    main = {v: parse_steps(s, spb) for v, s in t["pattern"].items()}
    fill = t["fill"]
    fill_steps = {v: parse_steps(s, spb) for v, s in fill["pattern"].items()} if fill else {}
    duration = max(1, round(bar_ticks / spb))
    notes: list[Note] = []
    bars: list[dict] = []
    for k in range(t["bars"]):
        bar_steps = {}
        for voice, steps in main.items():
            first = (k % (len(steps) // spb)) * spb  # longer patterns cycle bar by bar
            bar_steps[voice] = steps[first:first + spb]
        if fill and (k + 1) % fill["every"] == 0:
            bar_steps.update(fill_steps)
        counts: dict[str, int] = {}
        for voice in (v for v in VOICES if v in bar_steps):
            offset = ms_to_ticks(t["offset_ms"].get(voice, 0), bpm, PPQ)
            levels = t["velocity"].get(voice, {})
            for i, c in enumerate(bar_steps[voice]):
                if c == ".":
                    continue
                start = k * bar_ticks + step_tick(i, spb, bpb, PPQ, t["swing"]) + offset
                notes.append(Note(drum_map[voice], max(0, start), duration,
                                  levels.get(c, STEP_VELOCITY[c]), channel))
                counts[voice] = counts.get(voice, 0) + 1
        bars.append({"bar": k + 1, "hits": counts})
    return humanize(notes, t["humanize"], PPQ, t["seed"]), bars


def _summary(kind: str, bars: list[dict]) -> list[str]:
    if kind == "chords":
        return [f"Bar {b['bar']}: {b['chord']} = {' '.join(b['notes'])}" for b in bars]
    return [f"Bar {b['bar']}: " + (" ".join(f"{v}×{n}" for v, n in b["hits"].items())
                                   or "(no hits)") for b in bars]


def render_detailed(spec: dict) -> tuple[Song, list[str], list[dict]]:
    """Return (song, summary lines, per-track {"name", "bars"} details for JSON output)."""
    num, den = spec["time_signature"]
    bpb = num * 4 / den
    bar_ticks = round(bpb * PPQ)
    bpm = spec["bpm"]
    key = parse_key(spec["key"]) if spec["key"] else None
    tracks: list[Track] = []
    lines: list[str] = []
    details: list[dict] = []
    next_channel = 0
    for i, t in enumerate(spec["tracks"]):
        path = f"tracks[{i}]"
        if t["type"] == "drums":
            channel = DRUM_CHANNEL
            notes, bars = _drum_track(t, bpm, bpb, bar_ticks, channel)
        else:
            if next_channel == DRUM_CHANNEL:
                next_channel += 1
            channel = next_channel
            next_channel += 1
            notes, bars = _chord_track(t, path, key, bpm, bpb, bar_ticks, channel)
        for note in notes:
            try:
                validate_note(note)
            except MidiError as e:
                raise SpecError(path, str(e)) from None
        notes.sort(key=lambda n: (n.start, n.pitch))
        tracks.append(Track(t["name"], channel, notes))
        lines.extend(_summary(t["type"], bars))
        details.append({"name": t["name"], "bars": bars})
    return Song(bpm=bpm, time_signature=(num, den), tracks=tracks, ppq=PPQ), lines, details


def render(spec: dict) -> tuple[Song, list[str]]:
    """Render an already-validated spec to (Song, summary lines)."""
    song, lines, _ = render_detailed(spec)
    return song, lines
