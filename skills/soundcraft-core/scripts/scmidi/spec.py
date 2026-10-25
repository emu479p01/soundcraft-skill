"""Validate a JSON song spec and return a normalised copy with defaults applied.

Every problem raises SpecError naming the JSON field path, the bad value and
what is accepted, e.g. ``tracks[0].voicing: invalid value 'wide' (accepted: ...)``.
"""
from __future__ import annotations

import difflib
import math
import re
from typing import Any, Optional

from .drums import SOUNDCRAFT_UNSUPPORTED, VOICES, resolve_drum_map
from .rhythm import RHYTHMS, parse_steps
from .theory import VOICINGS, Key, TheoryError, parse_chord_token, parse_key

PPQ = 480
TOP_FIELDS = ("bpm", "time_signature", "key", "output", "tracks")
CHORD_FIELDS = ("name", "type", "progression", "chord_length", "voicing", "octave",
                "range", "rhythm", "steps", "velocity", "humanize", "seed", "repeat",
                "voice_leading", "bass_note", "strum_ms")
DRUM_FIELDS = ("name", "type", "pattern", "steps", "swing", "bars", "humanize", "seed",
               "offset_ms", "velocity", "fill", "drum_map")
TRACK_TYPES = ("chords", "drums")
DRUM_STEPS = (4, 8, 12, 16, 24, 32)
DENOMINATORS = (2, 4, 8, 16)
CUSTOM_STEPS = 16
MAX_TRACKS = 16
MAX_CHORD_TRACKS = 15  # MIDI channels 0-15 minus the drum channel 9
_LENGTH_RE = re.compile(r"^\s*(\d+(?:\.\d+)?)\s*(bars?|beats?)\s*$")
_LENGTH_ACCEPTED = '"1bar", "Nbars", "Nbeats" or a positive number of beats'


class SpecError(ValueError):
    """An invalid spec value. str(e) is "<path>: <message>"."""

    def __init__(self, path: str, message: str) -> None:
        super().__init__(f"{path}: {message}")
        self.path = path
        self.message = message


def _join(path: str, key: object) -> str:
    return f"{path}.{key}" if path else str(key)


def _check_fields(obj: dict, allowed: tuple[str, ...], path: str) -> None:
    for key in obj:
        if key not in allowed:
            close = difflib.get_close_matches(str(key), allowed, n=1)
            hint = f"did you mean {close[0]!r}?" if close else f"accepted: {', '.join(allowed)}"
            raise SpecError(_join(path, key), f"unknown field {key!r} ({hint})")


def _bad(path: str, value: Any, accepted: str) -> SpecError:
    return SpecError(path, f"invalid value {value!r} (accepted: {accepted})")


def _is_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _is_num(value: Any) -> bool:
    return (isinstance(value, (int, float)) and not isinstance(value, bool)
            and math.isfinite(value))


def _int(obj: dict, key: str, path: str, default: Any,
         lo: Optional[int] = None, hi: Optional[int] = None) -> int:
    value = obj.get(key, default)
    ok = _is_int(value) and (lo is None or lo <= value <= hi)
    if not ok:
        raise _bad(_join(path, key), value,
                   "an integer" if lo is None else f"an integer {lo}-{hi}")
    return value


def _num(obj: dict, key: str, path: str, default: float, lo: float, hi: float) -> float:
    value = obj.get(key, default)
    if not _is_num(value) or not lo <= value <= hi:
        raise _bad(_join(path, key), value, f"a number {lo}-{hi}")
    return value


def _bool(obj: dict, key: str, path: str, default: bool) -> bool:
    value = obj.get(key, default)
    if not isinstance(value, bool):
        raise _bad(_join(path, key), value, "true or false")
    return value


def _choice(obj: dict, key: str, path: str, default: Any, choices: tuple) -> Any:
    value = obj.get(key, default)
    if value not in choices or type(value) not in {type(c) for c in choices}:
        raise _bad(_join(path, key), value, ", ".join(str(c) for c in choices))
    return value


def _dict(value: Any, path: str, what: str) -> dict:
    if not isinstance(value, dict):
        raise _bad(path, value, what)
    return value


def _steps(text: Any, steps_per_bar: int, path: str) -> list[str]:
    if not isinstance(text, str):
        raise _bad(path, text, "a step string of x, X, g and .")
    try:
        return parse_steps(text, steps_per_bar)
    except ValueError as e:
        raise SpecError(path, str(e)) from None


def _beats(value: Any, path: str, beats_per_bar: float, unit: Optional[str] = None) -> float:
    """A length in quarter-note beats. unit forces a bare number to "beats" or "bars"."""
    beats: Optional[float] = None
    if _is_num(value) and value > 0:
        beats = value * beats_per_bar if unit == "bars" else float(value)
    elif isinstance(value, str) and unit is None:
        m = _LENGTH_RE.match(value)
        if m and float(m.group(1)) > 0:
            n = float(m.group(1))
            beats = n * beats_per_bar if m.group(2).startswith("bar") else n
    if beats is None or round(beats * PPQ) < 1:
        raise _bad(path, value, "a positive number" if unit else _LENGTH_ACCEPTED)
    return beats


def _progression(track: dict, path: str, key: Optional[Key], bpb: float) -> list[dict]:
    p = _join(path, "progression")
    if "progression" not in track:
        raise SpecError(p, "is required for a chords track (e.g. \"C - G - Am - F\")")
    default = _beats(track.get("chord_length", "1bar"), _join(path, "chord_length"), bpb)
    raw = track["progression"]
    if isinstance(raw, str):
        items: list = [t.strip() for t in re.split(r"[-|]", raw) if t.strip()]
    elif isinstance(raw, list):
        items = raw
    else:
        raise _bad(p, raw, "a list of chords or a string like \"C - G - Am - F\"")
    if not items:
        raise SpecError(p, "progression is empty")
    out = []
    for i, item in enumerate(items):
        ip = f"{p}[{i}]"
        if isinstance(item, str):
            token, token_path, beats = item.strip(), ip, default
        elif isinstance(item, dict):
            _check_fields(item, ("chord", "beats", "bars"), ip)
            token_path = f"{ip}.chord"
            token = item.get("chord")
            if not isinstance(token, str):
                raise _bad(token_path, token, "a chord symbol or roman numeral string")
            token = token.strip()
            if "beats" in item and "bars" in item:
                raise SpecError(ip, "use either 'beats' or 'bars', not both")
            if "beats" in item:
                beats = _beats(item["beats"], f"{ip}.beats", bpb, "beats")
            elif "bars" in item:
                beats = _beats(item["bars"], f"{ip}.bars", bpb, "bars")
            else:
                beats = default
        else:
            raise _bad(ip, item, "a chord string or {\"chord\", \"beats\"|\"bars\"}")
        try:
            parse_chord_token(token, key)
        except (TheoryError, ValueError) as e:
            raise SpecError(token_path, str(e)) from None
        out.append({"chord": token, "beats": beats})
    return out


def _chord_track(track: dict, path: str, key: Optional[Key], bpb: float) -> dict:
    _check_fields(track, CHORD_FIELDS, path)
    out = {"type": "chords", "name": track.get("name", "Chords")}
    out["progression"] = _progression(track, path, key, bpb)
    out["chord_length"] = track.get("chord_length", "1bar")
    out["voicing"] = _choice(track, "voicing", path, "close", VOICINGS)
    out["octave"] = _int(track, "octave", path, 4, 1, 7)
    rng = track.get("range", [48, 79])
    if (not isinstance(rng, list) or len(rng) != 2 or not all(_is_int(v) for v in rng)
            or not 0 <= rng[0] < rng[1] <= 127 or rng[1] - rng[0] < 12):
        raise _bad(_join(path, "range"), rng,
                   "[low, high] integers 0-127 with high - low >= 12")
    out["range"] = list(rng)
    out["rhythm"] = _choice(track, "rhythm", path, "pad", RHYTHMS)
    steps = track.get("steps")
    steps_path = _join(path, "steps")
    if out["rhythm"] == "custom":
        if steps is None:
            raise SpecError(steps_path, "is required when rhythm is 'custom' "
                                        "(a 16-step bar pattern like \"x...x...x...x...\")")
        parsed = _steps(steps, CUSTOM_STEPS, steps_path)
        if len(parsed) != CUSTOM_STEPS:
            raise SpecError(steps_path, f"custom rhythm needs exactly {CUSTOM_STEPS} steps "
                                        f"(one bar), got {len(parsed)}")
        if all(c == "." for c in parsed):
            raise SpecError(steps_path, "custom rhythm has no hits (only '.' rests)")
    elif steps is not None:
        raise SpecError(steps_path, f"is only used with rhythm 'custom' "
                                    f"(rhythm is {out['rhythm']!r})")
    out["steps"] = steps
    out["velocity"] = _int(track, "velocity", path, 90, 1, 127)
    out["humanize"] = _num(track, "humanize", path, 0, 0, 1)
    out["seed"] = _int(track, "seed", path, 1)
    out["repeat"] = _int(track, "repeat", path, 1, 1, 64)
    out["voice_leading"] = _bool(track, "voice_leading", path, True)
    out["bass_note"] = _bool(track, "bass_note", path, False)
    out["strum_ms"] = _num(track, "strum_ms", path, 0, 0, 100)
    return out


def _voice_steps(value: Any, path: str, spb: int, what: str, one_bar: bool) -> dict:
    pattern = _dict(value, path, f"an object of drum voice to step string ({what})")
    if not pattern:
        raise SpecError(path, f"is empty; give at least one voice ({', '.join(VOICES)})")
    _check_fields(pattern, VOICES, path)
    for voice, text in pattern.items():
        parsed = _steps(text, spb, _join(path, voice))
        if one_bar and len(parsed) != spb:
            raise SpecError(_join(path, voice),
                            f"a fill is one bar: expected {spb} steps, got {len(parsed)}")
    return dict(pattern)


def _drum_track(track: dict, path: str) -> dict:
    _check_fields(track, DRUM_FIELDS, path)
    out = {"type": "drums", "name": track.get("name", "Drums")}
    out["steps"] = spb = _choice(track, "steps", path, 16, DRUM_STEPS)
    if "pattern" not in track:
        raise SpecError(_join(path, "pattern"), "is required for a drums track")
    out["pattern"] = _voice_steps(track["pattern"], _join(path, "pattern"), spb,
                                  "pattern", one_bar=False)
    out["swing"] = _num(track, "swing", path, 0.5, 0.5, 0.75)
    out["bars"] = _int(track, "bars", path, 4, 1, 256)
    out["humanize"] = _num(track, "humanize", path, 0, 0, 1)
    out["seed"] = _int(track, "seed", path, 1)

    op = _join(path, "offset_ms")
    offsets = _dict(track.get("offset_ms", {}), op, "an object of voice to milliseconds")
    _check_fields(offsets, VOICES, op)
    out["offset_ms"] = {v: _num(offsets, v, op, 0, -50, 50) for v in offsets}

    vp = _join(path, "velocity")
    overrides = _dict(track.get("velocity", {}), vp, 'an object like {"hat": {"x": 85}}')
    _check_fields(overrides, VOICES, vp)
    out["velocity"] = {}
    for voice, levels in overrides.items():
        lp = _join(vp, voice)
        _check_fields(_dict(levels, lp, 'an object like {"x": 85, "g": 40}'), ("x", "X", "g"), lp)
        out["velocity"][voice] = {c: _int(levels, c, lp, None, 1, 127) for c in levels}

    fill = track.get("fill")
    fp = _join(path, "fill")
    if fill is not None:
        _check_fields(_dict(fill, fp, '{"every": N, "pattern": {...}}'), ("every", "pattern"), fp)
        if "every" not in fill or "pattern" not in fill:
            raise SpecError(fp, "needs both 'every' and 'pattern'")
        fill = {"every": _int(fill, "every", fp, None, 1, 64),
                "pattern": _voice_steps(fill["pattern"], _join(fp, "pattern"), spb,
                                        "one bar each", one_bar=True)}
    out["fill"] = fill

    drum_map = track.get("drum_map", "gm")
    try:
        resolve_drum_map(drum_map)
    except ValueError as e:
        raise SpecError(_join(path, "drum_map"), str(e)) from None
    if drum_map == "soundcraft":
        used = [(_join(path, "pattern"), out["pattern"])]
        if fill:
            used.append((_join(fp, "pattern"), fill["pattern"]))
        for base, pattern in used:
            for voice in pattern:
                if voice in SOUNDCRAFT_UNSUPPORTED:
                    raise SpecError(
                        _join(base, voice),
                        f"voice '{voice}' is not available in drum_synth "
                        f"({SOUNDCRAFT_UNSUPPORTED[voice]}); use drum_map \"gm\" "
                        f"with a GM plugin, or another voice.")
    out["drum_map"] = drum_map
    return out


def validate_spec(raw: dict) -> dict:
    """Return a normalised copy of raw with defaults applied; raise SpecError if invalid."""
    _dict(raw, "spec", "a JSON object")
    _check_fields(raw, TOP_FIELDS, "")
    spec: dict = {"bpm": _num(raw, "bpm", "", 120, 20, 300)}
    ts = raw.get("time_signature", [4, 4])
    if (not isinstance(ts, list) or len(ts) != 2 or not all(_is_int(v) for v in ts)
            or not 1 <= ts[0] <= 16 or ts[1] not in DENOMINATORS):
        raise _bad("time_signature", ts,
                   "[numerator 1-16, denominator 2, 4, 8 or 16], e.g. [4, 4]")
    spec["time_signature"] = list(ts)
    key_text = raw.get("key")
    key = None
    if key_text is not None:
        if not isinstance(key_text, str):
            raise _bad("key", key_text, 'null or a key name like "D minor"')
        try:
            key = parse_key(key_text)
        except (TheoryError, ValueError) as e:
            raise SpecError("key", str(e)) from None
    spec["key"] = key_text
    output = raw.get("output", "out.mid")
    if not isinstance(output, str) or not output.strip():
        raise _bad("output", output, "a non-empty file path string")
    spec["output"] = output

    tracks = raw.get("tracks")
    if not isinstance(tracks, list) or not 1 <= len(tracks) <= MAX_TRACKS:
        raise _bad("tracks", tracks, f"a list of 1-{MAX_TRACKS} track objects")
    bpb = ts[0] * 4 / ts[1]
    spec["tracks"] = []
    for i, track in enumerate(tracks):
        path = f"tracks[{i}]"
        _dict(track, path, "a track object")
        kind = track.get("type")
        if kind not in TRACK_TYPES:
            raise _bad(_join(path, "type"), kind, ", ".join(TRACK_TYPES))
        name = track.get("name", "")
        if not isinstance(name, str):
            raise _bad(_join(path, "name"), name, "a string")
        if kind == "chords":
            spec["tracks"].append(_chord_track(track, path, key, bpb))
        else:
            spec["tracks"].append(_drum_track(track, path))
    chord_tracks = sum(1 for t in spec["tracks"] if t["type"] == "chords")
    if chord_tracks > MAX_CHORD_TRACKS:
        raise SpecError("tracks", f"{chord_tracks} chords tracks; at most "
                                  f"{MAX_CHORD_TRACKS} fit in MIDI channels besides drums")
    return spec
