"""Step patterns, swing, humanize and chord rhythms. All times are in ticks."""
from __future__ import annotations

import random
from dataclasses import replace

from .model import Note

STEP_VELOCITY = {"x": 100, "X": 120, "g": 45}
_STEP_CHARS = "xXg."
RHYTHMS = ("pad", "block", "stabs", "arp-up", "arp-down", "arp-updown", "custom")


def parse_steps(pattern: str, steps_per_bar: int) -> list[str]:
    steps = [c for c in pattern if c not in " |"]
    for i, c in enumerate(steps, start=1):
        if c not in _STEP_CHARS:
            raise ValueError(
                f"invalid step character {c!r} at position {i} "
                f"(allowed: x, X, g, . and bar separators)")
    if steps_per_bar <= 0 or len(steps) % steps_per_bar != 0:
        raise ValueError(
            f"pattern has {len(steps)} steps, which is not a multiple of "
            f"{steps_per_bar} steps per bar")
    return steps


def step_tick(index: int, steps_per_bar: int, beats_per_bar: float,
              ppq: int, swing: float) -> int:
    d = beats_per_bar * ppq / steps_per_bar
    tick = index * d
    if index % 2 == 1:
        tick += round((2 * swing - 1) * d)
    return round(tick)


def ms_to_ticks(ms: float, bpm: float, ppq: int) -> int:
    return round(ms / 1000.0 * bpm / 60.0 * ppq)


def humanize(notes: list[Note], amount: float, ppq: int, seed: int) -> list[Note]:
    if amount == 0:
        return list(notes)
    rng = random.Random(seed)
    t_max = round(amount * ppq * 0.05)
    v_max = round(amount * 12)
    out = []
    for n in notes:
        dt = rng.randint(-t_max, t_max)
        dv = rng.randint(-v_max, v_max)
        out.append(replace(n, start=max(0, n.start + dt),
                           velocity=min(127, max(1, n.velocity + dv))))
    return out


def chord_hits(rhythm: str, length_ticks: int, ppq: int, beats_per_bar: float,
               custom_steps: list[str] | None, note_count: int = 3
               ) -> list[tuple[int, int, int | None, float]]:
    """Return (rel_start, duration, note_index or None for all notes, velocity_scale)."""
    if rhythm == "pad":
        return [(0, length_ticks, None, 1.0)]
    if rhythm == "block":
        dur = round(0.9 * ppq)
        return [(t, dur, None, 1.0) for t in range(0, length_ticks, ppq)]
    if rhythm == "stabs":
        return [(t, ppq // 2, None, 1.0)
                for t in (0, 2 * ppq) if t < length_ticks]
    if rhythm in ("arp-up", "arp-down", "arp-updown"):
        n = max(1, note_count)
        up = list(range(n))
        if rhythm == "arp-up":
            cycle = up
        elif rhythm == "arp-down":
            cycle = up[::-1]
        else:
            cycle = up + up[-2:0:-1]
        step = ppq // 4
        return [(t, step, cycle[k % len(cycle)], 1.0)
                for k, t in enumerate(range(0, length_ticks, step))]
    if rhythm == "custom":
        if not custom_steps:
            raise ValueError("rhythm 'custom' requires a non-empty step pattern")
        spb = len(custom_steps)
        bar_ticks = round(beats_per_bar * ppq)
        events: list[tuple[int, float]] = []
        bar = 0
        while bar * bar_ticks < length_ticks:
            for i, c in enumerate(custom_steps):
                if c == ".":
                    continue
                t = bar * bar_ticks + round(i * bar_ticks / spb)
                if t < length_ticks:
                    events.append((t, STEP_VELOCITY[c] / 100))
            bar += 1
        hits = []
        for k, (t, scale) in enumerate(events):
            end = events[k + 1][0] if k + 1 < len(events) else length_ticks
            hits.append((t, end - t, None, scale))
        return hits
    raise ValueError(f"unknown chord rhythm {rhythm!r} (allowed: {', '.join(RHYTHMS)})")
