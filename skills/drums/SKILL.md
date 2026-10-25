---
name: drums
description: Create genre-aware drum MIDI from a brief, choose a verified drum instrument and map, or export a .mid file when SoundCraft is unavailable.
---

## When to use

Use for drum patterns, fills, groove changes or drum MIDI export. Start with [genre grooves](references/grooves.md) and the [core schema and CLI](../soundcraft-core/SKILL.md); consult [exact SoundCraft commands](../soundcraft-core/references/soundcraft-commands.md) before MCP actions.

## Workflow

1. Translate the request into genre/reference, BPM, meter, bars, density, energy, swing, intended drum plugin and fill interval. Use the groove reference for missing values and tell the user what you chose. Ask at most two focused questions only when the missing information blocks a useful groove. Read `~/.soundcraft-skills/plugins.json` first when available: prefer an appropriate owned drum instrument, then built-in `drum_synth`. A filename in the corpus does not prove a runtime plugin ID or loadability. Never edit the corpus automatically.
2. Pick `drum_map: "soundcraft"` for built-in `drum_synth`; its custom map supports kick, snare, clap, hat, open_hat, pedal_hat, ride, crash and toms only. It has no rim, shaker, tambourine, cowbell or perc voice; do not substitute a different voice silently. Use `"gm"` only after verifying and confirming a GM-compatible plugin. Use a custom voice-to-note map only when the user supplies or confirms it. Verify the plugin's identity before assigning it.
3. For SoundCraft, preflight with `list_commands`, then read `inspect_session {detail: "full"}`. Use real track IDs and preserve existing tracks/clips; create a new track by default. Find any UNVERIFIED command with `list_commands` first. Use documented `track.new` / `mix.instrument` only with exact verified IDs and valid kinds. Re-read `inspect_session` after every mutation. Run commands from this skill's directory.
4. Save a fresh JSON spec and generate it with `python ../soundcraft-core/scripts/make_midi.py "/absolute/work/drums.json" --json`; the output path in the spec resolves beside the spec. Patterns repeat to the requested bar count. Use `fill: {"every": 4, ...}` or 8; the fill replaces listed voices on each Nth bar. Keep humanize subtle and seeded (for example, `humanize: 0.03`, `seed: 21`). For lo-fi/hip-hop, delay the snare slightly with `offset_ms`; keep house/techno hits tight at the grid. State the groove, map, BPM, swing, fill interval, plugin choice and reasons. Check the generated summary and intended voices.
5. After import, compare actual clip bounds with intended spec duration. If SoundCraft 0.12.1 omitted only a silent tail, extend only the new clip in verified Slip mode using its actual ID and computed absolute musical end (include import offset; use session tempo/timing), then re-inspect. Never truncate late notes, change edit mode globally, or mutate unrelated clips. For other modes or an omitted all-rest track, report the limitation and manual fallback; do not add dummy notes or claim success.
6. Generate → measure → adjust for at most **3 rounds total**. **FAIL:** invalid spec/notes, silent unsupported voice, failed import/instrument assignment, unintended silence (peak = -inf), or clipping (peak > 0 dBFS): correct the request or re-read session state before continuing. **WARN:** MCP/audio checks unavailable, uncertain mapping, or no confirmed GM instrument: disclose and continue with the local `.mid`. If MCP is unavailable, still export a `.mid` and give its absolute path for manual DAW import. Preserve tracks and clips; never claim an import or sound check that did not occur. After three rounds, report any unresolved failure and next step. Report chosen settings, why, absolute paths, measurements or skipped checks, and useful next action in plain language.

Reply to the user in the language they wrote in.

## Style table

Use [grooves.md](references/grooves.md) for pop; Thai pop/Luk thung; ballad; R&B/neo-soul; hip-hop; trap; lo-fi; house; techno; rock/indie; funk; jazz; latin/reggaeton; and afrobeats. BPM and patterns are adaptable starting points, not genre definitions. Cultural and acoustic timbres are approximations unless an appropriate confirmed instrument is available.

## Spec pattern

Four bars of a restrained straight pop groove. Save the spec in the user's working directory, then run the command from this skill's directory:

```json
{
  "bpm": 112, "time_signature": [4, 4], "output": "pop-drums.mid",
  "tracks": [{"name": "Pop Drums", "type": "drums", "steps": 16,
    "swing": 0.5, "bars": 4, "humanize": 0.03, "seed": 21,
    "pattern": {"kick": "x...x...x...x...", "snare": "....x.......x...",
      "hat": "x.x.x.x.x.x.x.x."},
    "fill": {"every": 4, "pattern": {"snare": "........x.x.XxXx"}},
    "drum_map": "soundcraft"}]
}
```

The fill patterns are one bar (16 steps) and replace only their named voice. `x` is normal, `X` accented, `g` ghost, and `.` rest. Drums use MIDI channel 10. Voice names and lengths are checked by the CLI; all maps and voices must match the selected instrument.

## Checks

Confirm the requested meter, tempo, total bars, pulse, kick/snare placement, swing, fill interval, supported map, and whether every pattern string is a multiple of steps per bar. Make fills every 4 or 8 bars unless the user requests another interval. Use a fixed seed and light humanize by default; too much timing/velocity variation can blur a tight groove. Keep lo-fi/hip-hop snares a little behind; house/techno stays tight. A valid MIDI file does not prove that an instrument loaded or that audio rendered.

## Limits

`drum_synth` is a custom map: 37 plays clap rather than rim, 44 plays closed hat, and unsupported GM notes for shaker, tambourine, cowbell and perc are silent. Never imply these voices sound as named on the built-in instrument. GM drum notes require a verified GM-compatible plugin; a custom map requires the user's confirmation. Do not infer culturally specific percussion from a genre label; ask for a reference and label approximations. No automatic installs, plugin downloads, corpus writes or harness configuration changes. The documented MCP command `track.new` can create an instrument track and `mix.instrument` can assign a verified instrument; discover any unverified command first. MIDI carries notes, not drum samples or audio.

## Related skills

Use [soundcraft-core](../soundcraft-core/SKILL.md) for MIDI export and command contracts, [soundcraft-setup](../soundcraft-setup/SKILL.md) for connectivity and file roots, [plugins](../plugins/SKILL.md) for verified inventory, and [thai-flavor](../thai-flavor/SKILL.md) for Thai musical context.

<!-- ideas: Korben00/ableton-producer-skills (MIT), Goldwaterfung/Stratawright (MIT); genre-oriented rhythm prompts and bounded iteration, rewritten independently for SoundCraft. -->
