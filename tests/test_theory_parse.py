from __future__ import annotations

import unittest

from scmidi.theory import (
    QUALITIES,
    Chord,
    Key,
    TheoryError,
    parse_chord,
    parse_chord_token,
    parse_key,
    parse_note,
    parse_roman,
    pitch_name,
)


def _shape(chord: Chord):
    return (chord.root, chord.intervals, chord.bass)


class ChordQualityTest(unittest.TestCase):
    def test_qualities(self):
        table = [
            ("C", (0, 4, 7)),
            ("Cm", (0, 3, 7)),
            ("Cdim", (0, 3, 6)),
            ("Caug", (0, 4, 8)),
            ("Csus2", (0, 2, 7)),
            ("Csus4", (0, 5, 7)),
            ("C5", (0, 7)),
            ("C6", (0, 4, 7, 9)),
            ("Cm6", (0, 3, 7, 9)),
            ("C7", (0, 4, 7, 10)),
            ("Cmaj7", (0, 4, 7, 11)),
            ("Cm7", (0, 3, 7, 10)),
            ("CmMaj7", (0, 3, 7, 11)),
            ("Cm7b5", (0, 3, 6, 10)),
            ("Cdim7", (0, 3, 6, 9)),
            ("C9", (0, 4, 7, 10, 14)),
            ("Cmaj9", (0, 4, 7, 11, 14)),
            ("Cm9", (0, 3, 7, 10, 14)),
            ("C11", (0, 4, 7, 10, 14, 17)),
            ("Cm11", (0, 3, 7, 10, 14, 17)),
            ("C13", (0, 4, 7, 10, 14, 21)),
            ("Cmaj13", (0, 4, 7, 11, 14, 21)),
            ("Cadd9", (0, 4, 7, 14)),
            ("Cadd11", (0, 4, 7, 17)),
        ]
        for symbol, intervals in table:
            with self.subTest(symbol=symbol):
                chord = parse_chord(symbol)
                self.assertEqual(chord.root, 0)
                self.assertEqual(chord.intervals, intervals)
                self.assertIsNone(chord.bass)
                self.assertEqual(chord.symbol, symbol)
                self.assertEqual(QUALITIES[symbol[1:]], intervals)
        self.assertEqual(len(QUALITIES), len(table))

    def test_alterations(self):
        table = [
            ("C7b9", (0, 4, 7, 10, 13)),
            ("C7#9", (0, 4, 7, 10, 15)),
            ("Cmaj7#11", (0, 4, 7, 11, 18)),
            ("C7b13", (0, 4, 7, 10, 20)),
            ("C7b5", (0, 4, 6, 10)),
            ("C7#5", (0, 4, 8, 10)),
            ("C7b9#11", (0, 4, 7, 10, 13, 18)),
            ("C7(b9)", (0, 4, 7, 10, 13)),
            ("C13b9", (0, 4, 7, 10, 13, 21)),
        ]
        for symbol, intervals in table:
            with self.subTest(symbol=symbol):
                self.assertEqual(parse_chord(symbol).intervals, intervals)

    def test_slash(self):
        chord = parse_chord("G/B")
        self.assertEqual((chord.root, chord.bass), (7, 11))
        self.assertEqual(chord.intervals, (0, 4, 7))
        self.assertEqual(_shape(parse_chord("Am7/G")), (9, (0, 3, 7, 10), 7))
        self.assertEqual(parse_chord("C/Bb").bass, 10)

    def test_aliases(self):
        pairs = [
            ("C♯m7", "C#m7"),
            ("B♭maj7", "Bbmaj7"),
            ("CΔ7", "Cmaj7"),
            ("CM7", "Cmaj7"),
            ("C-7", "Cm7"),
            ("Cmin7", "Cm7"),
            ("C°7", "Cdim7"),
            ("Cø7", "Cm7b5"),
            ("am7", "Am7"),
            # extra robustness for messy user input
            ("  Cmaj7 ", "Cmaj7"),
            ("CMaj7", "Cmaj7"),
            ("CMAJ7", "Cmaj7"),
            ("CΔ", "Cmaj7"),
            ("CΔ9", "Cmaj9"),
            ("CM9", "Cmaj9"),
            ("Cmaj", "C"),
            ("CM", "C"),
            ("Cmajor", "C"),
            ("Cmin", "Cm"),
            ("CMin7", "Cm7"),
            ("Cminor", "Cm"),
            ("C-", "Cm"),
            ("Cmi7", "Cm7"),
            ("Cø", "Cm7b5"),
            ("C-7b5", "Cm7b5"),
            ("C°", "Cdim"),
            ("Co7", "Cdim7"),
            ("C+", "Caug"),
            ("CmM7", "CmMaj7"),
            ("Cmmaj7", "CmMaj7"),
            ("Cm(maj7)", "CmMaj7"),
            ("C-Δ7", "CmMaj7"),
            ("CminMaj7", "CmMaj7"),
            ("Csus", "Csus4"),
            ("CSus4", "Csus4"),
            ("CADD9", "Cadd9"),
            ("C DIM", "Cdim"),
            ("G / B", "G/B"),
            ("g/b", "G/B"),
            ("bbmaj7", "Bbmaj7"),
            ("D♭/A♭", "Db/Ab"),
        ]
        for left, right in pairs:
            with self.subTest(left=left, right=right):
                self.assertEqual(_shape(parse_chord(left)), _shape(parse_chord(right)))

    def test_case_of_m_matters(self):
        self.assertEqual(parse_chord("CM7").intervals, (0, 4, 7, 11))
        self.assertEqual(parse_chord("Cm7").intervals, (0, 3, 7, 10))
        self.assertEqual(parse_chord("Cm").intervals, (0, 3, 7))
        self.assertEqual(parse_chord("CM").intervals, (0, 4, 7))

    def test_roots(self):
        self.assertEqual(parse_chord("F#7").root, 6)
        self.assertEqual(parse_chord("Ebm").root, 3)
        self.assertEqual(parse_chord("Cb").root, 11)
        self.assertEqual(parse_chord("B#").root, 0)

    def test_bad_chord_message(self):
        with self.assertRaises(TheoryError) as ctx:
            parse_chord("Xm7")
        self.assertIn("Xm7", str(ctx.exception))
        self.assertIn("root", str(ctx.exception))
        with self.assertRaises(TheoryError) as ctx:
            parse_chord("Cblah")
        self.assertIn("Cblah", str(ctx.exception))
        self.assertIn("quality", str(ctx.exception))
        with self.assertRaises(TheoryError) as ctx:
            parse_chord("C/X")
        self.assertIn("C/X", str(ctx.exception))
        self.assertIn("bass", str(ctx.exception))
        for bad in ["", "   ", "C7b11", "C/", "Cmaj7/"]:
            with self.subTest(bad=bad):
                with self.assertRaises(TheoryError):
                    parse_chord(bad)

    def test_theory_error_is_value_error(self):
        self.assertTrue(issubclass(TheoryError, ValueError))


class NoteTest(unittest.TestCase):
    def test_parse_note(self):
        self.assertEqual(parse_note("C"), 0)
        self.assertEqual(parse_note("C#"), 1)
        self.assertEqual(parse_note("Db"), 1)
        self.assertEqual(parse_note("D♭"), 1)
        self.assertEqual(parse_note("F♯"), 6)
        self.assertEqual(parse_note("b"), 11)
        self.assertEqual(parse_note(" bb "), 10)
        self.assertEqual(parse_note("B#"), 0)
        self.assertEqual(parse_note("Cb"), 11)
        for bad in ["H", "", "C##", "Cx"]:
            with self.subTest(bad=bad):
                with self.assertRaises(TheoryError) as ctx:
                    parse_note(bad)
                self.assertIn(repr(bad), str(ctx.exception))

    def test_pitch_name(self):
        self.assertEqual(pitch_name(60), "C4")
        self.assertEqual(pitch_name(61), "C#4")
        self.assertEqual(pitch_name(21), "A0")
        self.assertEqual(pitch_name(0), "C-1")
        self.assertEqual(pitch_name(127), "G9")
        for bad in [-1, 128]:
            with self.assertRaises(TheoryError):
                pitch_name(bad)


class KeyTest(unittest.TestCase):
    def test_keys(self):
        self.assertEqual(parse_key("D minor"), Key(2, "minor"))
        self.assertEqual(parse_key("Dm"), Key(2, "minor"))
        self.assertEqual(parse_key("D min"), Key(2, "minor"))
        self.assertEqual(parse_key("F# major"), Key(6, "major"))
        self.assertEqual(parse_key("C"), Key(0, "major"))
        self.assertEqual(parse_key("Bb"), Key(10, "major"))
        self.assertEqual(parse_key("Bb"), Key(10, "major"))
        self.assertEqual(parse_key("  d   minor "), Key(2, "minor"))
        self.assertEqual(parse_key("D Minor"), Key(2, "minor"))
        self.assertEqual(parse_key("Bbm"), Key(10, "minor"))
        self.assertEqual(parse_key("E♭ major"), Key(3, "major"))
        self.assertEqual(parse_key("A maj"), Key(9, "major"))
        self.assertEqual(parse_key("A aeolian"), Key(9, "minor"))

    def test_bad_key(self):
        with self.assertRaises(TheoryError) as ctx:
            parse_key("H minor")
        self.assertIn("H minor", str(ctx.exception))
        self.assertIn("tonic", str(ctx.exception))
        with self.assertRaises(TheoryError) as ctx:
            parse_key("D dorian")
        self.assertIn("D dorian", str(ctx.exception))
        self.assertIn("mode", str(ctx.exception))


class RomanTest(unittest.TestCase):
    def test_roman_minor(self):
        key = Key(2, "minor")
        expected = [
            ("i", 2, QUALITIES["m"]),
            ("VI", 10, QUALITIES[""]),
            ("III", 5, QUALITIES[""]),
            ("VII", 0, QUALITIES[""]),
        ]
        for numeral, root, intervals in expected:
            with self.subTest(numeral=numeral):
                chord = parse_roman(numeral, key)
                self.assertEqual((chord.root, chord.intervals, chord.bass), (root, intervals, None))

    def test_roman_major_sevenths(self):
        key = Key(0, "major")
        expected = [
            ("ii7", 2, "m7", "Dm7"),
            ("V7", 7, "7", "G7"),
            ("Imaj7", 0, "maj7", "Cmaj7"),
            ("bVII", 10, "", "Bb"),
            ("V/V", 2, "", "D"),
            ("viiø7", 11, "m7b5", "Bm7b5"),
        ]
        for numeral, root, quality, symbol in expected:
            with self.subTest(numeral=numeral):
                chord = parse_roman(numeral, key)
                self.assertEqual(chord.root, root)
                self.assertEqual(chord.intervals, QUALITIES[quality])
                self.assertIsNone(chord.bass)
                self.assertEqual(chord.symbol, symbol)

    def test_roman_more_suffixes(self):
        key = Key(0, "major")
        cases = [
            ("iii", 4, QUALITIES["m"]),
            ("vii°", 11, QUALITIES["dim"]),
            ("viio7", 11, QUALITIES["dim7"]),
            ("vii°7", 11, QUALITIES["dim7"]),
            ("viidim", 11, QUALITIES["dim"]),
            ("III+", 4, QUALITIES["aug"]),
            ("IV9", 5, QUALITIES["9"]),
            ("ii9", 2, QUALITIES["m9"]),
            ("imaj7", 0, QUALITIES["mMaj7"]),
            ("IM7", 0, QUALITIES["maj7"]),
            ("#iv°", 6, QUALITIES["dim"]),
            ("V7b9", 7, (0, 4, 7, 10, 13)),
            ("Vsus4", 7, QUALITIES["sus4"]),
            ("vii°/V", 6, QUALITIES["dim"]),
            ("V/ii", 9, QUALITIES[""]),
            (" V7 / IV ", 0, QUALITIES["7"]),
        ]
        for numeral, root, intervals in cases:
            with self.subTest(numeral=numeral):
                chord = parse_roman(numeral, key)
                self.assertEqual((chord.root, chord.intervals), (root, intervals))

    def test_roman_in_other_keys(self):
        self.assertEqual(parse_roman("V", Key(2, "minor")).root, 9)
        self.assertEqual(parse_roman("iv", Key(9, "minor")).root, 2)
        self.assertEqual(parse_roman("IV", Key(6, "major")).root, 11)

    def test_bad_roman(self):
        key = Key(0, "major")
        with self.assertRaises(TheoryError) as ctx:
            parse_roman("Vblah", key)
        self.assertIn("Vblah", str(ctx.exception))
        self.assertIn("quality", str(ctx.exception))
        with self.assertRaises(TheoryError) as ctx:
            parse_roman("VIII", key)
        self.assertIn("VIII", str(ctx.exception))
        with self.assertRaises(TheoryError):
            parse_roman("Vi", key)


class ChordTokenTest(unittest.TestCase):
    def test_roman_with_key(self):
        key = Key(0, "major")
        self.assertEqual(parse_chord_token("V7", key).root, 7)
        self.assertEqual(parse_chord_token("bVII", key).root, 10)

    def test_symbol_with_key(self):
        key = Key(0, "major")
        self.assertEqual(_shape(parse_chord_token("G/B", key)), (7, (0, 4, 7), 11))
        self.assertEqual(_shape(parse_chord_token("bm7", key)), (11, (0, 3, 7, 10), None))
        self.assertEqual(_shape(parse_chord_token("Bb", key)), (10, (0, 4, 7), None))

    def test_symbol_without_key(self):
        self.assertEqual(parse_chord_token("Dm9", None).intervals, QUALITIES["m9"])

    def test_roman_without_key(self):
        with self.assertRaises(TheoryError) as ctx:
            parse_chord_token("V7", None)
        self.assertIn("V7", str(ctx.exception))
        self.assertIn("key", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
