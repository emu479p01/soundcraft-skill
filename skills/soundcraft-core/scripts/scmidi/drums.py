"""Drum voice names and note maps (GM and SoundCraft drum_synth)."""
from __future__ import annotations

VOICES = ("kick", "snare", "clap", "rim", "hat", "open_hat", "pedal_hat", "ride",
          "crash", "tom_hi", "tom_mid", "tom_low", "shaker", "tambourine",
          "cowbell", "perc")

GM_MAP = {
    "kick": 36, "snare": 38, "clap": 39, "rim": 37, "hat": 42, "open_hat": 46,
    "pedal_hat": 44, "ride": 51, "crash": 49, "tom_hi": 50, "tom_mid": 47,
    "tom_low": 45, "shaker": 70, "tambourine": 54, "cowbell": 56, "perc": 75,
}

# drum_synth uses a custom map; only voices with a distinct sound are listed.
SOUNDCRAFT_MAP = {
    "kick": 36, "snare": 38, "clap": 39, "hat": 42, "open_hat": 46,
    "pedal_hat": 44, "ride": 51, "crash": 49, "tom_hi": 50, "tom_mid": 47,
    "tom_low": 45,
}

SOUNDCRAFT_UNSUPPORTED = {
    "rim": "37 plays a clap",
    "shaker": "70 is unmapped, silent",
    "tambourine": "54 is unmapped, silent",
    "cowbell": "56 is unmapped, silent",
    "perc": "75 is unmapped, silent",
}


def resolve_drum_map(value: str | dict) -> dict[str, int]:
    if isinstance(value, str):
        if value == "gm":
            return dict(GM_MAP)
        if value == "soundcraft":
            return dict(SOUNDCRAFT_MAP)
        raise ValueError(f"unknown drum map {value!r} (use \"gm\", \"soundcraft\" or an object)")
    if not isinstance(value, dict):
        raise ValueError("drum map must be \"gm\", \"soundcraft\" or an object of voice to note")
    result = dict(GM_MAP)
    for voice, note in value.items():
        if voice not in GM_MAP:
            raise ValueError(f"unknown drum voice {voice!r} (allowed: {', '.join(VOICES)})")
        if isinstance(note, bool) or not isinstance(note, int) or not 0 <= note <= 127:
            raise ValueError(f"drum voice {voice!r} note {note!r} must be an integer 0-127")
        result[voice] = note
    return result
