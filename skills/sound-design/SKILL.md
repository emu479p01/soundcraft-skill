---
name: sound-design
description: Design subtractive-synth patches, map verified controls to SoundCraft's built-in synth, and save track presets safely.
---

## When to use

Use for a requested synth sound, patch recipe, or SoundCraft subtractive-synth preset. Read [synth recipes](references/synth-recipes.md) for eight starting points and supported values.

## Workflow

1. Run commands from this skill's directory. Read [the command reference](../soundcraft-core/references/soundcraft-commands.md). Preflight with MCP `list_commands`; read `inspect_session` before editing. For a requested external instrument, check the owned plugin corpus first and treat its entries as candidates, not proof they load. Follow [plugins](../plugins/SKILL.md) for inventory and exact runtime discovery. Give generic synth guidance only when an external synth is selected. For effects, use EQ → compressor → saturation → modulation → delay → reverb as a starting order.
2. Preserve existing tracks and instruments. Use the existing intended instrument track only when the request or existing authorization identifies it; otherwise create a uniquely named instrument track if requested. Before setting parameters, discover the exact command with `list_commands` if marked UNVERIFIED. The documented built-in mapping is `mix.instrument` with `params` or `mix.instrument_param` with `{track, param, value}`. Apply only the 19 documented `subtractive_synth` IDs and ranges; re-read `inspect_session` after each change. Filter type, LFO, and unison are not among them. For any missing range query, discover via `list_commands` first; never invent a query, setter, or parameter. `osc2_detune` is oscillator cents detune, not unison.
3. Iterate sound design and any requested audio check for at most three rounds. Report **FAIL** for invalid commands, failed assignment, or a failed requested render; stop and explain. Report **WARN** when a requested control, runtime range, external plugin, or audio check cannot be verified. Do not claim an 808 pitch drop: no pitch-envelope parameter is exposed. Save only when requested, using verified `track.save_preset` with `{path, track}`; this writes a SoundCraft track preset, not a per-plugin preset. Use a fresh approved path inside the write root. Never overwrite unless the user authorized it and the documented overwrite behavior is confirmed.
4. If MCP is unavailable and the task is music-relevant, provide a `.mid` fallback when useful and Python is available; MIDI carries notes, not synth patches or rendered sound. Give the absolute path and explain that manual instrument assignment and preset saving remain. Report actual applied values, unavailable controls, file path, checks, and next step in plain language.

Reply to the user in the language they wrote in.

## Style table

| Goal | Starting recipe |
|---|---|
| Sustained and soft | Pad |
| Short and bright | Pluck |
| Forward melody | Lead |
| Rounded low end | Bass |
| 808 or sub | 808/sub |
| Pitched transient | Keys |
| Bold ensemble-like tone | Brass-ish |
| Repeating sequence | Arp |

## Spec pattern

N/A — recipes are parameter sets, not MIDI specs. See [synth recipes](references/synth-recipes.md).

## Checks

- Confirm the target track and plugin with `inspect_session` after assignment; re-read after parameter changes.
- Check all proposed values against the reference ranges. Runtime range discovery is unverified; use only controls and ranges documented there unless runtime evidence is available.
- After saving, report the actual path and that `track.save_preset` saves the whole track state. Do not claim an audio render without a successful render and measured result.

## Limits

SoundCraft's built-in `subtractive_synth` exposes 19 parameters. It does not expose verified filter type, LFO, or unison controls. Generic external-synth suggestions in the reference are not SoundCraft setters. The built-in has no verified pitch envelope; an 808/sub recipe can provide oscillator/sub fundamentals and a short filter transient, but not an 808 pitch-drop sweep. Hosted instrument controls and per-plugin preset saving are not established by the built-in parameter map.

## Related skills

Use [soundcraft-setup](../soundcraft-setup/SKILL.md) for MCP and file roots, [plugins](../plugins/SKILL.md) for corpus and runtime plugin discovery, and [soundcraft-core](../soundcraft-core/SKILL.md) for MIDI fallback.

<!-- ideas: Korben00/ableton-producer-skills (MIT); generic patch planning rewritten for SoundCraft's verified command and parameter limits. -->
