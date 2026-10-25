---
name: chords
description: Use when composing chord progressions from symbols, Roman numerals or natural-language briefs, reharmonizing existing harmony, or exporting chord MIDI for SoundCraft.
---

## When to use

Turn harmony requests into playable MIDI and, when available, SoundCraft tracks. Read [genre starting points](references/genres.md) for the requested style, [core schema and CLI](../soundcraft-core/SKILL.md) for field details, and [exact command contracts](../soundcraft-core/references/soundcraft-commands.md) before MCP operations.

## Workflow

1. Extract key/scale, BPM, bars, genre/feel, mood, density, energy arc and instrument. Accept typed symbols (including slash bass), Roman numerals **with a key**, or a natural-language brief. Preserve supplied chords unless reharmonization was requested. Fill gaps from the style reference; otherwise use C major, 100 BPM, 4/4, four bars, one chord per bar, moderate density, steady energy, close voicing, range `[48,79]`, velocity 80 and `pad`. State the choices and reasons. For missing Roman key or genuinely blocking ambiguity, ask at most 1–2 focused questions; do not silently assign a key to supplied numerals.
2. Read `~/.soundcraft-skills/plugins.json` if present before selecting an instrument. Honor an explicit instrument choice, otherwise prefer an appropriate owned instrument, then `subtractive_synth`. A scanned filename is not a runtime plugin ID or proof of loadability. Missing/unreadable corpus: disclose fallback; do not modify it or scan/write it automatically. Free plugins in the reference are optional suggestions, never automatic downloads or installs.
3. For MCP, preflight `list_commands`, then `inspect_session {detail: "full"}`. Read actual track names/IDs, kinds, clips, transport and plugins; verify exact instrument IDs before loading. For any UNVERIFIED operation, find it with `list_commands` first, including external plugin listing and parameter-range queries. Stop transport with `execute` command `transport.stop`, params `{}`, before structural edits when needed. Preserve existing tracks/clips; default to new tracks. Re-read `inspect_session` after every mutation.
4. **Reharmonization:** first read the original harmony and melody/context; then announce exactly **one** strategy before generating or changing notes, for example: “I'll add sevenths and ninths while preserving the roots and phrase lengths.” Apply only that strategy. Other choices include modal interchange, tritone substitution or passing diminished harmony; use the reference to choose one that fits. For “reuse Verse,” authorization covers that existing track: resolve the unique actual track, preserve unrelated clips and instrument, and discover an exact supported clip-edit/import-target operation before editing. `file.import_midi` has no documented target-track parameter. If safe reuse is unavailable, deliver a separate candidate `.mid` and explain the blocked edit; do not delete Verse or substitute a new imported track and claim reuse. When necessary, export the actual MIDI track via `file.export_midi {path: absoluteOriginalMidiPath, tracks: [actualTrack]}` and analyze with the core CLI; discover an alternative if its kind cannot be exported.
5. Run commands from this skill's directory. Save specs and artifacts in the user's working directory, never the installed skill/plugin cache. Choose fresh filenames. Generate with `python ../soundcraft-core/scripts/make_midi.py "/absolute/work/chords.json" --json`; relative `output` resolves beside that spec. Review the note summary against harmony, duration and range. MCP unavailable: still generate the local `.mid` and provide its absolute path for manual DAW import.
6. With file access enabled, import via `execute` command `file.import_midi`, params `{path: absoluteMidiPath}`; re-read state and identify actual new tracks from the response and session. Compare imported clip bounds with intended spec duration. If SoundCraft 0.12.1 omitted only a silent tail, extend only the new clip in verified Slip mode using its actual ID and computed absolute musical end (include import offset; use session tempo/timing); re-inspect. Never truncate late notes, change edit mode globally, or touch unrelated clips. For other modes or an omitted all-rest track, report the limitation and manual fallback; no dummy notes or claimed success. On an instrument track assign `mix.instrument {track: actualTrack, plugin: exactVerifiedId}` through `execute`, then re-read. For incompatible track kinds, discover supported routing/conversion; stop that step if unavailable. Default manifests grant no file roots: use `soundcraft-setup` for explicitly authorized existing workspace roots or the desktop bridge. On denied access, retain local MIDI and report manual import/setup options. Every software install or harness config change requires explicit authorization for that scope, honoring prior consent.
7. Generate → measure → adjust for at most **3 rounds total**. Validate spec/notes each round; with MCP and write access, `bounce_mix {path: absoluteWavPath, format: "wav"}` over the intended span, then read peak dBFS and integrated LUFS. **FAIL:** invalid notes, failed import/instrument, unintended silence (peak = -inf), clipping (peak > 0 dBFS). Stop the failing step, correct the request or re-read session state as appropriate; unresolved FAIL after round 3: stop and ask. **WARN:** unavailable MCP/audio checks, uncertain harmonic analysis; disclose and continue local export. Report plainly what changed, chosen values and why, absolute paths, measurements or unperformed checks, and next step.

Reply to the user in the language they wrote in.

## Style table

Use the requested section of [genres.md](references/genres.md): pop; Thai pop/Luk thung; ballad; R&B/neo-soul; hip-hop; trap; lo-fi; house; techno; rock/indie; funk; jazz; latin/reggaeton; afrobeats. Each supplies BPM/feel, three symbol/Roman choices, voicing/rhythm and instrument suggestions. These are adaptable starting points, not genre definitions.

## Spec pattern

Four bars of the typed input `Am7–Fmaj7–C–G/B`, with stated defaults:

```json
{
  "bpm": 100, "time_signature": [4, 4], "key": "C major",
  "output": "chords.mid",
  "tracks": [{"name": "Chords", "type": "chords",
    "progression": ["Am7", "Fmaj7", "C", "G/B"], "chord_length": "1bar",
    "voicing": "close", "range": [48, 79], "octave": 4,
    "rhythm": "pad", "velocity": 80, "voice_leading": true}]
}
```

For `ii7–V7–Imaj7` in C major, use progression `["ii7","V7","Imaj7"]`; assign explicit durations when fitting a four-bar phrase. Use arrays for symbols containing `-`, since string progressions split on hyphens. Genre JSON examples are full runnable specs, not audio patches.

## Checks

Confirm chords and melody tensions, phrase length, note range, velocity and bass intent. Roman degrees follow the selected key's scale: `VI` in A minor is F; `bVI` would be Fb/E. Use `rootless` only for suitable seventh/extended harmonies with an actual separate bass part supplying roots; default to rooted voicings otherwise. Rootless mode removes roots, not an automatic jazz arrangement. Slash bass can fall below the upper-voice range. Chord `stabs` hits beats 1 and 3; use a 16-character `custom` pattern for offbeats. Custom hits sustain until the next hit; shorten the instrument envelope for short comping. MIDI validation is not evidence of audible output.

## Limits

No automatic replacement, corpus writes, installers or harness edits. Built-in synth has no verified LFO/unison controls; use `sound-design` for supported parameters. Range-query tooling is UNVERIFIED: discover first; if absent, use only source-verified built-in ranges and disclose that runtime ranges were unavailable. Hosted instruments do not accept `mix.instrument_param`. Cultural and acoustic timbres here are labeled synth approximations; ask for a musical reference when fidelity matters.

## Related skills

Use `soundcraft-core` for schema/export/analysis, `soundcraft-setup` for connectivity and file roots, `plugins` for inventory, `sound-design` for patches, `drums` for accompaniment, `theory-coach` for interpretation and `thai-flavor` for Thai idioms.

<!-- ideas: Korben00/ableton-producer-skills (MIT), Goldwaterfung/Stratawright (MIT); brief mapping, state inspection and bounded measurement, rewritten for SoundCraft. -->
