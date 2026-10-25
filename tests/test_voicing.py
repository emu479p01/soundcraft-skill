from __future__ import annotations

import unittest

from scmidi.theory import VOICINGS, TheoryError, parse_chord, voice_chord

DEFAULT_RANGE = (48, 79)
_NAMES = ("C", "Db", "D", "Eb", "E", "F", "Gb", "G", "Ab", "A", "Bb", "B")


def _voice(symbol, voicing="close", octave=4, range_=DEFAULT_RANGE, **kwargs):
    return voice_chord(parse_chord(symbol), voicing, octave, range_, **kwargs)


class VoicingTests(unittest.TestCase):
    def test_close_c_major_oct4(self):
        self.assertEqual(_voice("C"), ([60, 64, 67], None))

    def test_open(self):
        upper, _ = _voice("Cmaj7", "open")
        self.assertEqual(upper, [60, 67, 71, 76])

    def test_drop2(self):
        upper, _ = _voice("Cmaj7", "drop2", 4, (48, 79))
        self.assertEqual(upper, [55, 60, 64, 71])

    def test_rootless_dm9(self):
        upper, _ = _voice("Dm9", "rootless")
        self.assertTrue(upper)
        for note in upper:
            self.assertGreaterEqual(note, 56)
            self.assertLessEqual(note, 74)
        self.assertNotIn(2, {note % 12 for note in upper})

    def test_slash_bass(self):
        upper, bass = _voice("G/B")
        self.assertIsNotNone(bass)
        self.assertEqual(bass % 12, 11)
        self.assertLessEqual(bass, min(upper) - 5)

    def test_bass_note_flag_uses_root(self):
        upper, bass = _voice("C", bass_note=True)
        self.assertEqual(bass, 48)
        self.assertEqual(upper, [60, 64, 67])

    def test_voice_leading_small_motion(self):
        upper, _ = _voice("F", previous=[60, 64, 67])
        self.assertEqual(upper, [60, 65, 69])

    def test_voice_leading_off_keeps_root_position(self):
        upper, _ = _voice("F", previous=[60, 64, 67], voice_leading=False)
        self.assertEqual(upper, [65, 69, 72])

    def test_long_cycle_stays_in_range(self):
        symbols = []
        for step in range(12):
            tonic = (step * 5) % 12  # around the cycle of fourths
            symbols += [
                _NAMES[(tonic + 2) % 12] + "m7",
                _NAMES[(tonic + 7) % 12] + "7",
                _NAMES[tonic] + "maj7",
            ]
        symbols = symbols[:32]
        self.assertEqual(len(symbols), 32)
        for voicing in VOICINGS:
            previous = None
            for symbol in symbols:
                upper, _ = _voice(symbol, voicing, previous=previous)
                self.assertEqual(upper, sorted(set(upper)), (voicing, symbol))
                for note in upper:
                    self.assertGreaterEqual(note, 48, (voicing, symbol))
                    self.assertLessEqual(note, 79, (voicing, symbol))
                previous = upper

    def test_narrow_range_folds(self):
        upper, _ = _voice("C13", range_=(60, 72))
        self.assertTrue(upper)
        self.assertEqual(len(upper), len(set(upper)))
        self.assertEqual(upper, sorted(upper))
        for note in upper:
            self.assertGreaterEqual(note, 60)
            self.assertLessEqual(note, 72)

    def test_spread(self):
        upper, _ = _voice("C", "spread")
        self.assertEqual(upper, [48, 64, 79])

    def test_range_too_narrow_rejected(self):
        with self.assertRaises(TheoryError) as ctx:
            _voice("C", range_=(60, 65))
        self.assertIn("range", str(ctx.exception))

    def test_unknown_voicing(self):
        with self.assertRaises(TheoryError) as ctx:
            _voice("C", "cluster")
        message = str(ctx.exception)
        self.assertIn("voicing", message)
        for name in ("close", "open", "drop2", "spread", "rootless"):
            self.assertIn(name, message)


if __name__ == "__main__":
    unittest.main()
