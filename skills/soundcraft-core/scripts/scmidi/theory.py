"""Music theory helpers: notes, chord symbols, keys and roman numerals.

All pitch classes are integers 0-11 with C = 0. MIDI note 60 is C4 (middle C).
Every error raised here is a TheoryError whose message names the offending
text and the part that was wrong, so callers can re-raise it with a field path.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional

__all__ = [
    "QUALITIES",
    "Chord",
    "Key",
    "TheoryError",
    "parse_chord",
    "parse_chord_token",
    "parse_key",
    "parse_note",
    "parse_roman",
    "pitch_name",
]


class TheoryError(ValueError):
    """Raised for an unparseable note, chord symbol, key or roman numeral."""


# Canonical quality suffix -> semitones above the root (sorted, including 0).
QUALITIES: dict[str, tuple[int, ...]] = {
    "": (0, 4, 7),
    "m": (0, 3, 7),
    "dim": (0, 3, 6),
    "aug": (0, 4, 8),
    "sus2": (0, 2, 7),
    "sus4": (0, 5, 7),
    "5": (0, 7),
    "6": (0, 4, 7, 9),
    "m6": (0, 3, 7, 9),
    "7": (0, 4, 7, 10),
    "maj7": (0, 4, 7, 11),
    "m7": (0, 3, 7, 10),
    "mMaj7": (0, 3, 7, 11),
    "m7b5": (0, 3, 6, 10),
    "dim7": (0, 3, 6, 9),
    "9": (0, 4, 7, 10, 14),
    "maj9": (0, 4, 7, 11, 14),
    "m9": (0, 3, 7, 10, 14),
    "11": (0, 4, 7, 10, 14, 17),
    "m11": (0, 3, 7, 10, 14, 17),
    "13": (0, 4, 7, 10, 14, 21),
    "maj13": (0, 4, 7, 11, 14, 21),
    "add9": (0, 4, 7, 14),
    "add11": (0, 4, 7, 17),
}

# Alteration -> (interval removed if present, interval added).
_ALTERATIONS: dict[str, tuple[int, int]] = {
    "b5": (7, 6),
    "#5": (7, 8),
    "b9": (14, 13),
    "#9": (14, 15),
    "#11": (17, 18),
    "b13": (21, 20),
}

_SHARP_NAMES = ("C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B")
_FLAT_NAMES = ("C", "Db", "D", "Eb", "E", "F", "Gb", "G", "Ab", "A", "Bb", "B")
_LETTERS = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}

_MAJOR_SCALE = (0, 2, 4, 5, 7, 9, 11)
_MINOR_SCALE = (0, 2, 3, 5, 7, 8, 10)
_NUMERALS = ("I", "II", "III", "IV", "V", "VI", "VII")

_ROOT_RE = re.compile(r"^([A-Ga-g][#b]?)")
_NOTE_RE = re.compile(r"^[A-Ga-g][#b]?$")
_QUALITY_ALT = "|".join(re.escape(q) for q in sorted(QUALITIES, key=len, reverse=True) if q)
_ALTERATION_ALT = "|".join(re.escape(a) for a in sorted(_ALTERATIONS, key=len, reverse=True))
_QUALITY_RE = re.compile(rf"^({_QUALITY_ALT})?((?:{_ALTERATION_ALT})*)$")
_ALTERATION_RE = re.compile(_ALTERATION_ALT)

_NUMERAL_ALT = "VII|VI|V|IV|III|II|I|vii|vi|v|iv|iii|ii|i"
_ROMAN_RE = re.compile(rf"^([b#]?)({_NUMERAL_ALT})([^/]*)(?:/([b#]?)({_NUMERAL_ALT}))?$")

# Quality used for a lowercase (minor) numeral, keyed by the plain quality.
_MINOR_OF = {"": "m", "6": "m6", "7": "m7", "maj7": "mMaj7", "9": "m9", "11": "m11"}
# Qualities with a major third and no minor counterpart in QUALITIES.
_MAJOR_ONLY = {"aug", "maj9", "13", "maj13", "add9", "add11"}

# Tonics whose conventional key signature uses flats.
_FLAT_KEYS = {"major": {5, 10, 3, 8, 1, 6}, "minor": {2, 7, 0, 5, 10, 3}}

_ACCEPTED_QUALITIES = ", ".join(q or "(none = major triad)" for q in QUALITIES)
_ACCEPTED_ALTERATIONS = ", ".join(_ALTERATIONS)


@dataclass(frozen=True)
class Chord:
    root: int
    intervals: tuple[int, ...]
    bass: Optional[int]
    symbol: str


@dataclass(frozen=True)
class Key:
    tonic: int
    mode: str  # "major" or "minor"

    @property
    def name(self) -> str:
        names = _FLAT_NAMES if self.tonic in _FLAT_KEYS[self.mode] else _SHARP_NAMES
        return f"{names[self.tonic]} {self.mode}"


def _unicode_accidentals(text: str) -> str:
    return text.replace("♯", "#").replace("♭", "b")


def _note_value(name: str) -> int:
    value = _LETTERS[name[0].upper()]
    if len(name) > 1:
        value += 1 if name[1] == "#" else -1
    return value % 12


def parse_note(name: str) -> int:
    """Return the pitch class (0-11) of a note name like 'C', 'F#', 'Db', 'b♭'."""
    text = _unicode_accidentals(str(name).strip())
    if not _NOTE_RE.match(text):
        raise TheoryError(
            f"Invalid note name {name!r}: expected a letter A-G with an optional # or b"
        )
    return _note_value(text)


def pitch_name(midi: int) -> str:
    """Return the sharp-spelled name of a MIDI note, e.g. 60 -> 'C4' (middle C)."""
    if not isinstance(midi, int) or isinstance(midi, bool) or not 0 <= midi <= 127:
        raise TheoryError(f"Invalid MIDI note {midi!r}: expected an integer 0-127")
    return f"{_SHARP_NAMES[midi % 12]}{midi // 12 - 1}"


def _normalise_quality(text: str) -> str:
    """Map the many spellings of a chord quality onto the canonical QUALITIES keys."""
    q = re.sub(r"[(),]", "", text)
    q = q.replace("ø7", "m7b5").replace("ø", "m7b5")
    q = q.replace("°", "dim")
    q = re.sub(r"Δ(?=\d)", "maj", q)
    q = q.replace("Δ", "maj7")
    q = re.sub(r"(?i)major", "maj", q)
    q = re.sub(r"(?i)minor", "m", q)
    q = re.sub(r"(?i)maj", "maj", q)
    q = re.sub(r"(?i)min", "m", q)
    q = re.sub(r"(?i)^mi(?=\d|maj|M|$)", "m", q)
    for word in ("dim", "aug", "sus", "add"):
        q = re.sub(rf"(?i){word}", word, q)
    # Any capital M left over is the major-seventh shorthand ("CM7", "CmM7", "CM").
    q = q.replace("M", "maj")
    if q.startswith("-"):
        q = "m" + q[1:]
    elif q.startswith("+"):
        q = "aug" + q[1:]
    elif q.startswith("o"):
        q = "dim" + q[1:]
    q = q.replace("mmaj", "mMaj")
    if q == "maj":
        q = ""
    elif q == "sus":
        q = "sus4"
    return q


def _split_quality(text: str) -> Optional[tuple[str, list[str]]]:
    """Split a normalised suffix into (quality, alterations), or None if invalid."""
    match = _QUALITY_RE.match(text)
    if match is None:
        return None
    return match.group(1) or "", _ALTERATION_RE.findall(match.group(2))


def _intervals(quality: str, alterations: list[str]) -> tuple[int, ...]:
    tones = set(QUALITIES[quality])
    for alteration in alterations:
        removed, added = _ALTERATIONS[alteration]
        tones.discard(removed)
        tones.add(added)
    return tuple(sorted(tones))


def _quality_error(kind: str, token: str, suffix: str, detail: str) -> TheoryError:
    return TheoryError(
        f"Invalid {kind} {token!r}: unrecognised quality {suffix!r}{detail}. "
        f"Accepted qualities: {_ACCEPTED_QUALITIES}; "
        f"alterations: {_ACCEPTED_ALTERATIONS}"
    )


def parse_chord(symbol: str) -> Chord:
    """Parse a chord symbol such as 'Dm9', 'Bbmaj7', 'A7b9' or 'G/B'."""
    original = str(symbol).strip()
    text = re.sub(r"\s+", "", _unicode_accidentals(original))
    # "Cm/maj7" spells the minor-major seventh, not a slash chord.
    text = re.sub(r"(?i)(m|-|min)/maj", r"\1maj", text)
    root_match = _ROOT_RE.match(text)
    if root_match is None:
        bad = text[:1] or "(empty)"
        raise TheoryError(
            f"Invalid chord symbol {original!r}: root {bad!r} is not a note name "
            f"(expected a letter A-G with an optional # or b)"
        )
    root_text = root_match.group(1)
    rest = text[root_match.end():]
    bass: Optional[int] = None
    if "/" in rest:
        rest, bass_text = rest.rsplit("/", 1)
        if not _NOTE_RE.match(bass_text):
            raise TheoryError(
                f"Invalid chord symbol {original!r}: bass note {bass_text!r} after '/' "
                f"is not a note name (expected a letter A-G with an optional # or b)"
            )
        bass = _note_value(bass_text)
    parts = _split_quality(_normalise_quality(rest))
    if parts is None:
        raise _quality_error("chord symbol", original, rest, f" after root {root_text!r}")
    quality, alterations = parts
    return Chord(_note_value(root_text), _intervals(quality, alterations), bass, original)


def parse_key(text: str) -> Key:
    """Parse a key such as 'D minor', 'Dm', 'D min', 'F# major', 'C' or 'Bb'."""
    original = str(text).strip()
    norm = _unicode_accidentals(original)
    root_match = _ROOT_RE.match(norm)
    if root_match is None:
        bad = norm.split()[0] if norm.split() else "(empty)"
        raise TheoryError(
            f"Invalid key {original!r}: tonic {bad!r} is not a note name "
            f"(expected a letter A-G with an optional # or b)"
        )
    mode_text = norm[root_match.end():].strip()
    lowered = mode_text.lower()
    if mode_text in ("", "M") or lowered in ("major", "maj", "ionian"):
        mode = "major"
    elif mode_text == "m" or lowered in ("minor", "min", "aeolian"):
        mode = "minor"
    else:
        raise TheoryError(
            f"Invalid key {original!r}: mode {mode_text!r} is not recognised "
            f"(accepted: major, minor, maj, min, m)"
        )
    return Key(_note_value(root_match.group(1)), mode)


def _degree_root(
    accidental: str, numeral: str, tonic: int, mode: str, raised_seventh: bool = False
) -> int:
    scale = _MINOR_SCALE if mode == "minor" else _MAJOR_SCALE
    index = _NUMERALS.index(numeral.upper())
    offset = 11 if raised_seventh and index == 6 else scale[index]
    shift = {"": 0, "#": 1, "b": -1}[accidental]
    return (tonic + offset + shift) % 12


def _spell(root: int, key: Key, accidental: str) -> str:
    if accidental == "b" or (accidental != "#" and key.tonic in _FLAT_KEYS[key.mode]):
        return _FLAT_NAMES[root]
    return _SHARP_NAMES[root]


def _roman_match(token: str) -> Optional[re.Match]:
    text = re.sub(r"\s+", "", _unicode_accidentals(str(token).strip()))
    return _ROMAN_RE.match(text)


def parse_roman(numeral: str, key: Key) -> Chord:
    """Parse a roman numeral ('ii7', 'bVII', 'V/V', 'viiø7') relative to a key.

    Case gives the quality (upper = major, lower = minor). Degrees come from the
    major scale, or the natural minor scale in a minor key. 'X/Y' builds X on
    degree Y of the key, treating Y as a major key if uppercase, minor if lowercase.
    In a secondary chord, degree VII is always the raised leading tone (11 semitones
    above Y), so vii°/vi in C is G#dim, while the key's own numerals stay natural.
    """
    original = str(numeral).strip()
    match = _roman_match(original)
    if match is None:
        raise TheoryError(
            f"Invalid roman numeral {original!r} in key {key.name}: expected an optional "
            f"b/# then I-VII (major) or i-vii (minor), a quality, and optionally /degree"
        )
    accidental, degree, suffix, target_acc, target = match.groups()
    tonic, mode = key.tonic, key.mode
    if target is not None:
        tonic = _degree_root(target_acc, target, key.tonic, key.mode)
        mode = "major" if target.isupper() else "minor"
    root = _degree_root(accidental, degree, tonic, mode, raised_seventh=target is not None)

    parts = _split_quality(_normalise_quality(suffix))
    if parts is None:
        raise _quality_error("roman numeral", original, suffix, f" after numeral {degree!r}")
    quality, alterations = parts
    if degree.islower():
        if quality in _MINOR_OF:
            quality = _MINOR_OF[quality]
        elif quality in _MAJOR_ONLY:
            raise _quality_error(
                "roman numeral", original, suffix,
                f" for a lowercase (minor) numeral {degree!r}",
            )
    symbol = _spell(root, key, accidental) + quality + "".join(alterations)
    return Chord(root, _intervals(quality, alterations), None, symbol)


def parse_chord_token(token: str, key: Optional[Key]) -> Chord:
    """Parse a progression token: a roman numeral when a key is set, else a chord symbol."""
    if _roman_match(token) is not None:
        if key is None:
            raise TheoryError(
                f"Roman numeral {str(token).strip()!r} needs a 'key' to be set "
                f"(e.g. \"key\": \"C major\"); otherwise use a chord symbol like 'G7'"
            )
        return parse_roman(token, key)
    return parse_chord(token)
