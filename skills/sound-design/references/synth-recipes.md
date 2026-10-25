# Subtractive synth recipes

These are starting values for SoundCraft's built-in `subtractive_synth`, based on the verified command reference. Values map only to its 19 documented parameters. Wave choices are `0` Saw, `1` Square, `2` Sine, `3` Triangle. Time values are milliseconds; sustain, resonance, mix, and envelope amount are percent. All values below are within documented ranges. The built-in amp attack minimum is **0.5 ms**, not 0 ms.

## Recipe map

| Sound | `osc1_wave` | `osc2_wave` | `osc2_semitones` | `osc2_detune` (cents) | `osc_mix` | `cutoff` (Hz) | `resonance` (%) | Amp A / D / S / R | Filter A / D / S / R | `filter_env_amount` (%) | `glide` (ms) | `velocity` (%) | `level` (dB) |
|---|---:|---:|---:|---:|---:|---:|---:|---|---|---:|---:|---:|---:|
| Pad | 0 | 3 | 0 | 7 | 35 | 1800 | 18 | 80 / 900 / 72 / 1400 | 300 / 1200 / 35 / 900 | 24 | 0 | 65 | -9 |
| Pluck | 1 | 0 | 12 | 4 | 28 | 5200 | 24 | 0.5 / 180 / 0 / 100 | 0.5 / 240 / 0 / 120 | 55 | 0 | 78 | -7 |
| Lead | 0 | 1 | 12 | 6 | 40 | 6200 | 28 | 8 / 260 / 62 / 180 | 5 / 220 / 20 / 150 | 32 | 45 | 76 | -8 |
| Bass | 1 | 2 | -12 | 0 | 20 | 700 | 15 | 3 / 260 / 72 / 180 | 2 / 280 / 25 / 160 | 18 | 0 | 72 | -8 |
| 808/sub | 2 | 2 | -12 | 0 | 0 | 180 | 8 | 0.5 / 500 / 90 / 220 | 0.5 / 180 / 5 / 120 | 42 | 0 | 90 | -10 |
| Keys | 1 | 3 | 12 | 3 | 32 | 3600 | 22 | 0.5 / 420 / 18 / 280 | 0.5 / 360 / 8 / 220 | 28 | 0 | 72 | -8 |
| Brass-ish | 0 | 1 | 0 | 8 | 42 | 3000 | 20 | 18 / 320 / 68 / 240 | 8 / 300 / 38 / 220 | 38 | 0 | 78 | -9 |
| Arp | 1 | 0 | 12 | 5 | 30 | 4600 | 26 | 0.5 / 150 / 12 / 100 | 0.5 / 180 / 6 / 100 | 34 | 0 | 75 | -8 |

`A / D / S / R` means attack, decay, sustain, release. The parameter names are `amp_attack`, `amp_decay`, `amp_sustain`, `amp_release` and `filter_attack`, `filter_decay`, `filter_sustain`, `filter_release`. Parameter `velocity` is a percent response setting; it is distinct from MIDI note velocity. Parameter `level` is dB.

## Unsupported and external-only controls

Filter type, LFO rate/depth/shape, and unison voice count are not in the exposed 19 parameters. Do not add keys for these to `mix.instrument` or call imagined setters. Discover commands with MCP `list_commands` before attempting any uncertain operation; the command reference says range-query tooling is unverified. If no verified control exists, leave it unapplied and say so. The generic ideas below are external-synth concepts only, not SoundCraft values or commands:

| Sound | Generic filter type / intent | Generic LFO | Generic unison / detune |
|---|---|---|---|
| Pad | Low-pass, mellow; start near 1.8 kHz | UNVERIFIED: slow, shallow pitch or filter motion | UNVERIFIED: several voices, subtle detune |
| Pluck | Low-pass, bright opening transient | UNVERIFIED: off or very subtle | UNVERIFIED: off or slight detune |
| Lead | Low-pass, moderately resonant | UNVERIFIED: subtle vibrato if wanted | UNVERIFIED: a few voices, restrained detune |
| Bass | Low-pass, restrained resonance | UNVERIFIED: off | UNVERIFIED: mono or off; keep low end centered |
| 808/sub | Low-pass, low resonance | UNVERIFIED: off; pitch drop needs a pitch envelope | UNVERIFIED: off for stable sub |
| Keys | Low-pass, moderate brightness | UNVERIFIED: off or subtle | UNVERIFIED: off or slight detune |
| Brass-ish | Low-pass, moderate resonance | UNVERIFIED: subtle motion only | UNVERIFIED: a few voices, modest detune |
| Arp | Low-pass, bright enough for note definition | UNVERIFIED: slight filter motion if desired | UNVERIFIED: restrained; avoid obscuring fast notes |

The built-in `osc2_detune` is oscillator-2 tuning offset in cents, range -100..100. It is **not unison**. The 808/sub row uses supported oscillator and filter-envelope settings only; the synth exposes no pitch-envelope field, so it cannot make a pitch-drop transient through this mapping.

## Applying a recipe

1. Preflight MCP with `list_commands`, then read `inspect_session`. Keep existing tracks and clips intact. Confirm the target is an instrument track assigned to `subtractive_synth`; if not, use a new track unless the user explicitly authorized replacement.
2. Apply supported values via `mix.instrument {track, plugin: "subtractive_synth", params: {...}}` when creating/assigning, or `mix.instrument_param {track, param, value}` for an existing built-in instrument. The parameter command names are in the command reference. Use only the recipe's supported columns, then re-read `inspect_session` to verify actual chosen values where state exposes them. Never imply values outside state were applied.
3. Save only on request with `track.save_preset {path, track}`. It saves a SoundCraft **track** preset (including the track instrument/state), not a per-plugin sound preset. Use a new file path inside an approved automation write root. Do not overwrite a file unless overwrite semantics have been verified and the user authorized it. Re-read state after saving.
4. If runtime ranges are needed, discover the relevant command using `list_commands` first; do not invent a range-query command. If the MCP tool is unavailable, provide the recipe as a manual starting point and, for a music-relevant request, consider a `.mid` handoff. A MIDI file carries note events only; it does not store these patch values.

<!-- ideas: Korben00/ableton-producer-skills (MIT); synth recipe concepts rewritten as generic guidance, with unsupported controls explicitly separated from verified SoundCraft parameters. -->
