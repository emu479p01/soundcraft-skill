---
name: thai-flavor
description: Create culturally careful Thai and Isan inspired chord and drum MIDI sketches, with explicit modal choices, supported voice mappings, and fusion limits.
---

## When to use

Use when a user asks for Thai pop, Luk thung, Mor lam, a named khaen lai, or Sam cha influence in a MIDI sketch. Read [Thai style references](references/thai-styles.md), then hand the chord and drum specs to [chords](../chords/SKILL.md) and [drums](../drums/SKILL.md). A style name alone does not establish a mode, instrument, or authentic arrangement.

## Workflow

1. Identify the named style, reference recording or artist, desired mood, length, tempo and whether the user wants traditional context or a contemporary fusion. If absent, state a creative starting choice and invite a specific reference when closer idiom is important.
2. Read the relevant style entry and its source notes. Keep the selected tonal center and melodic contour distinct from the pitch-class set; use the provided pinned khaen sets only as reference transcriptions, not universal tuning or practice. Thai pop and Luk thung do not have one required pentatonic set. Explain that a pentatonic melody does not constrain every harmony note or describe all music in either style.
3. Write separate chord and drum JSON specs using the documented schemas. Omit `key` for modal-symbol sketches. Use only supported `drum_synth` voices with `drum_map: "soundcraft"`; label every proxy and its reason. Do not claim a proxy reproduces a traditional instrument. Hand specs to `chords` and `drums`; this skill does not invoke a direct note-generation MCP command.
4. For any SoundCraft MCP use, preflight with `list_commands`, read `inspect_session {detail: "full"}`, preserve existing tracks and clips, act only on verified state, then re-read state after each mutation. Find any unverified command with `list_commands` first. Run CLI commands from the relevant skill directory.
5. Generate → check → adjust for at most 3 rounds. **FAIL:** invalid specs/notes, unsupported or silent voice, failed import/instrument assignment, silence or clipping; correct the spec or re-read state before retrying. **WARN:** no MCP/audio check, no compatible instrument, or uncertain idiom; disclose and continue with a local `.mid` fallback. Report choices, why, files, checks and remaining uncertainty in plain language.

Reply to the user in the language they wrote in.

## Style table

See [Thai style references](references/thai-styles.md) for six complete chord and drum examples. They are equal-tempered, quantized 4/4 creative sketches, not transcriptions or definitions. Pinned Mor lam pitch sets and cited research are described there.

## Spec pattern

Use the complete per-style examples in [Thai style references](references/thai-styles.md). Their specs use only schema fields accepted by `soundcraft-core`; mode sketches omit `key` rather than implying a major/minor key.

## Checks

Confirm center and pitch-class order, progression spelling, BPM, 4/4 duration, voice support, exact drum map and proxy rationale. `soundcraft` supports kick, snare, clap, hat, open_hat, pedal_hat, ride, crash, tom_hi, tom_mid and tom_low only; it has no cowbell, perc, rim, shaker or tambourine. Ching→ride/open_hat and chap→crash/open_hat approximate brightness or open/closed contrast. Klong yao, thon and rammana→toms approximate pitched body only. Validate each embedded spec with `python tools/lint_skills.py skills/thai-flavor`; generated MIDI is not evidence of cultural accuracy or audible instrument identity.

## Limits

The pinned Lai yai, Lai noi and Lai sut sanaen sets are transcription references from the cited research, not fixed tuning or universal performance practice. Yai and noi share a pitch set but differ in center, drone and melodic contour; do not treat them as interchangeable. Long-way styles can be plaintive or slow/free; example BPMs are starting points. Western triads, equal temperament, quantized 4/4 and GM-like tom/cymbal proxies are fusion approximations, not authentic traditional progressions or percussion. Sam cha (สามช่า) is not sam chan and does not automatically mean 3/4. If a user requests cultural precision beyond these references, state what is uncertain and ask for a performer or recording reference.

## Related skills

Use [chords](../chords/SKILL.md) for harmony specs, [drums](../drums/SKILL.md) for supported grooves, and [soundcraft-core](../soundcraft-core/SKILL.md) for MIDI validation and export.

<!-- ideas: Korben00/ableton-producer-skills (MIT), Goldwaterfung/Stratawright (MIT); style-index and groove-prompt ideas rewritten independently for SoundCraft. -->
