from __future__ import annotations

import unittest

from scmidi.drums import (GM_MAP, SOUNDCRAFT_MAP, SOUNDCRAFT_UNSUPPORTED,
                          VOICES, resolve_drum_map)
from scmidi.model import Note
from scmidi.rhythm import (chord_hits, humanize, ms_to_ticks, parse_steps,
                           step_tick)


class RhythmTests(unittest.TestCase):
    def test_parse_steps_ok_and_bad_char(self):
        self.assertEqual(len(parse_steps("x...x...", 8)), 8)
        with self.assertRaises(ValueError) as cm:
            parse_steps("x..q", 4)
        self.assertIn("position 4", str(cm.exception))

    def test_parse_steps_length_mismatch(self):
        with self.assertRaises(ValueError):
            parse_steps("x..", 4)

    def test_parse_steps_ignores_bar_separators(self):
        self.assertEqual(len(parse_steps("x... | x...", 4)), 8)

    def test_swing(self):
        self.assertEqual(step_tick(1, 16, 4, 480, 0.5), 120)
        self.assertEqual(step_tick(1, 16, 4, 480, 0.75), 180)
        self.assertEqual(step_tick(2, 16, 4, 480, 0.75), 240)

    def test_ms_to_ticks(self):
        self.assertEqual(ms_to_ticks(25, 120, 480), 24)

    def test_humanize_deterministic_and_clamped(self):
        notes = [Note(36, i * 480, 100, 127 if i % 2 else 1, 9) for i in range(16)]
        a = humanize(notes, 1.0, 480, 1)
        self.assertEqual(a, humanize(notes, 1.0, 480, 1))
        self.assertNotEqual(a, humanize(notes, 1.0, 480, 2))
        self.assertEqual(humanize(notes, 0, 480, 1), notes)
        self.assertTrue(all(n.start >= 0 and 1 <= n.velocity <= 127 for n in a))
        first = humanize([Note(36, 0, 10, 1, 9)] * 50, 1.0, 480, 3)
        self.assertTrue(all(n.start >= 0 and n.velocity >= 1 for n in first))

    def test_chord_hits_each_rhythm(self):
        bar = 1920
        kw = dict(ppq=480, beats_per_bar=4, custom_steps=None)
        self.assertEqual(len(chord_hits("pad", bar, **kw)), 1)
        self.assertEqual(len(chord_hits("block", bar, **kw)), 4)
        self.assertEqual(len(chord_hits("stabs", bar, **kw)), 2)
        up = chord_hits("arp-up", bar, **kw)
        self.assertEqual(len(up), 16)
        ud = chord_hits("arp-updown", bar, note_count=3, **kw)
        self.assertEqual([h[2] for h in ud[:6]], [0, 1, 2, 1, 0, 1])
        up3 = chord_hits("arp-up", bar, note_count=3, **kw)
        self.assertEqual([h[2] for h in up3[:4]], [0, 1, 2, 0])

    def test_chord_hits_custom(self):
        steps = parse_steps("x..." + "X..." + "g..." + "x...", 16)
        hits = chord_hits("custom", 1920, 480, 4, steps)
        self.assertEqual(len(hits), 4)
        self.assertEqual(hits[0], (0, 480, None, 1.0))
        self.assertEqual(hits[1][3], 1.2)


class DrumTests(unittest.TestCase):
    def test_drum_maps(self):
        self.assertEqual(resolve_drum_map("gm")["kick"], 36)
        m = resolve_drum_map({"kick": 24})
        self.assertEqual((m["kick"], m["snare"]), (24, 38))
        with self.assertRaises(ValueError) as cm:
            resolve_drum_map({"cowbel": 56})
        self.assertIn("cowbel", str(cm.exception))
        with self.assertRaises(ValueError) as cm:
            resolve_drum_map({"kick": 128})
        self.assertIn("kick", str(cm.exception))
        self.assertEqual(len(VOICES), 16)
        self.assertEqual(set(GM_MAP), set(VOICES))

    def test_soundcraft_map(self):
        m = resolve_drum_map("soundcraft")
        self.assertEqual(m["kick"], 36)
        self.assertNotIn("cowbell", m)
        self.assertEqual(set(SOUNDCRAFT_UNSUPPORTED), set(VOICES) - set(SOUNDCRAFT_MAP))
        self.assertEqual(set(SOUNDCRAFT_UNSUPPORTED),
                         {"rim", "shaker", "tambourine", "cowbell", "perc"})
        m["kick"] = 1
        self.assertEqual(SOUNDCRAFT_MAP["kick"], 36)


if __name__ == "__main__":
    unittest.main()
