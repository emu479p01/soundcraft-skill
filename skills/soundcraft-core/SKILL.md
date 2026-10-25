---
name: soundcraft-core
description: Use when exporting chords or drums to a .mid file, using the local MIDI generation, analysis or plugin scan CLIs, or checking SoundCraft MCP command contracts.
---

## When to use

Export requested music directly, including when MCP is offline. Use the CLI table below for MIDI analysis or plugin inventory. Read [the command reference](references/soundcraft-commands.md) before SoundCraft operations; it contains exact params, plugin IDs, drum mappings and recovery classes.

## Workflow

1. Establish the requested output and existing working directory. Choose fresh output filenames; overwrite existing files only when authorized. For music, choose and disclose missing tempo, meter, length, range and instrument assumptions. Run commands from this skill's directory. Python must be 3.9+; no packages are needed.
2. For SoundCraft work, preflight with `list_commands`, then read `inspect_session` for actual track names/IDs and transport state. Preserve existing tracks/clips; import to new tracks unless replacement was requested. Stop transport before structural changes if necessary. Find any command marked UNVERIFIED in the reference with `list_commands` first. Parameter-range discovery is UNVERIFIED: discover it first; never invent a range-query command or parameter. If unavailable, use only source-verified built-in ranges from the reference and disclose that runtime ranges were not read.
3. For export, save a spec, run `python scripts/make_midi.py spec.json --json`, and review notes, bars and range. If MCP is unavailable, complete this local export anyway and give the absolute `.mid` path for manual drag/import into another DAW. For scan-only or analysis-only tasks, return the real inventory/analysis; do not fabricate a musical MIDI fallback.
4. Import only after checking file access: default manifest args `["mcp"]` grant no read/write roots. Follow `soundcraft-setup` for explicitly approved roots on the existing working directory; plugin installation alone grants no import, bounce or preset access. On path denial, retain the local MIDI, explain the missing root and offer manual import or approved setup.
5. With access, use `execute` command `file.import_midi`, params `{path: absoluteMidiPath}`. Re-read `inspect_session`, match the import's returned tracks to actual new tracks, and use their real identifiers. Assign the exact verified instrument with `mix.instrument {track, plugin}` only on an instrument track; if the imported track kind cannot accept it, discover a supported routing/conversion operation before proceeding. Re-read after every change. Never guess track IDs or claim an instrument was assigned on error.
6. When audio checking is requested/appropriate and a write root is enabled, call `bounce_mix {path: absoluteWavPath, format: "wav"}` for the intended span. Read returned peak dBFS and integrated LUFS. Generate → measure → adjust for at most 3 rounds total: FAIL for invalid MIDI, failed import/instrument, silence (peak = -inf), or clipping (peak > 0 dBFS); WARN for unavailable MCP/audio checks or uncertain analysis. After 3 failing rounds, stop and ask about the unresolved issue. Report what happened, chosen values and why, absolute file paths, measured results or unperformed checks, and next step in plain language.

Reply to the user in the language they wrote in.

## Style table

N/A — shared tools; use `chords` or `drums` for genre choices.

## Spec pattern

Save as `spec.json`; this example is four bars, one chord per bar:

```json
{
  "bpm": 120, "time_signature": [4, 4], "key": "C major",
  "output": "smoke.mid",
  "tracks": [{"name": "Smoke Chords", "type": "chords",
    "progression": ["C", "G", "Am", "F"], "chord_length": "1bar",
    "voicing": "close", "octave": 4, "rhythm": "pad", "velocity": 80}]
}
```

For “export Am7–Fmaj7–C–G/B,” replace the progression array with those four symbols and disclose the retained defaults. Use arrays for chord spellings containing a minus sign; string progressions split on `-` or `|`.

| JSON field (scope) | Accepted values; default when omitted |
|---|---|
| `bpm`, `time_signature` (song) | 20–300; 120. `[numerator, denominator]`: 1–16 and 2/4/8/16; `[4,4]` |
| `key`, `output`, `tracks` (song) | Key name or null (required for Roman numerals); null. Nonempty output path; CLI resolution below. Required 1–16 track objects, at most 15 chord tracks |
| `type`, `name` (track) | Required `chords` or `drums`; name defaults to Chords/Drums |
| `progression`, `chord_length` (chords) | Required chord array or separated string. Items: symbol or `{chord, beats}` / `{chord, bars}` (positive, mutually exclusive durations); default length `1bar`, also positive beats number or `Nbars`/`Nbeats` |
| Chord symbols | Triads, m/dim/aug/sus2/sus4/5/6/m6, 7/maj7/m7/mMaj7/m7b5/dim7, 9/maj9/m9/11/m11/13/maj13/add9/add11, alterations b5/#5/b9/#9/#11/b13, slash bass; Roman numerals including bVII and V/V with `key` |
| `voicing`, `octave`, `range` (chords) | close/open/drop2/spread/rootless; close. Integer 1–7; 4. MIDI `[low,high]`, 0–127, span ≥12; `[48,79]`. C4 = 60 |
| `rhythm`, `steps` (chords) | block/pad/stabs/arp-up/arp-down/arp-updown/custom; pad. Custom requires exactly 16 characters `xXg.`; steps forbidden for other rhythms |
| `velocity`, `repeat`, `voice_leading`, `bass_note`, `strum_ms` (chords) | Integer 1–127; 90. Repeat 1–64; 1. Booleans; true/false respectively. Strum 0–100 ms; 0. Bass adds root one octave below |
| `humanize`, `seed` (either track type) | 0–1; 0. Integer seed; 1 (repeatable timing/velocity variation) |
| `pattern`, `steps`, `bars` (drums) | Required voice→step-string object; lengths multiples of steps. Steps 4/8/12/16/24/32; 16. Bars 1–256; 4 |
| Drum voices / characters | kick/snare/clap/rim/hat/open_hat/pedal_hat/ride/crash/tom_hi/tom_mid/tom_low/shaker/tambourine/cowbell/perc. `x`=100, `X`=120, `g`=45, `.`=rest |
| `swing`, `offset_ms`, `velocity` (drums) | Swing 0.5–0.75; 0.5. Voice→offset -50..50 ms; `{}`. Voice→`{x, X, g}` overrides 1–127; `{}` |
| `fill`, `drum_map` (drums) | Optional `{every: 1–64, pattern: {voice: oneBarSteps}}` replaces specified voices on every Nth bar. Map gm/soundcraft/voice→MIDI note 0–127; gm. Built-in soundcraft rejects rim/shaker/tambourine/cowbell/perc; use supported voices or a compatible GM plugin |

## Checks

All three CLIs support `-h`/`--help` (exit 0); argparse usage errors exit 2. Errors go to stderr.

| CLI (prefix with `python scripts/`) | Args and results | Actual exit codes |
|---|---|---|
| `make_midi.py` | `SPEC.json` or `-` for stdin; `--out PATH` overrides output, relative to cwd; `--json` emits `{output, tracks}` with per-bar details, otherwise text notes and absolute output path. Spec-relative `output` resolves beside spec; absent output uses spec stem `.mid`, or cwd `out.mid` for stdin | 0 written; 2 invalid spec/JSON (nothing written); 1 I/O/unexpected error |
| `analyze_midi.py` | `FILE.mid`; `--window BEATS` positive finite quarter-note beats (1); `--track NAME` exact name; `--key "D minor"` for Roman numerals; `--json`. Text key/runner-up and chord spans, or JSON `key`, `runner_up`, `key_source`, `score_kind`, `chords`; excludes channel index 9 | 0 analyzed; 2 unreadable/invalid MIDI or analysis options; 1 unexpected error |
| `scan_plugins.py` | `--extra-dir DIR` repeatable, adds to standard OS roots; `--json` emits `plugins`, `unsupported`, `missing_dirs`, otherwise grouped text/warnings. `--write-corpus [PATH]` writes timestamp/platform plus inventory; default `~/.soundcraft-skills/plugins.json`. Categories inferred from filenames; no binary is opened/executed | 0 success including missing-root/unsupported-format warnings; 2 invalid arguments/root; 1 I/O/unexpected error |

Validate before writing: MIDI pitch 0–127, velocity 1–127, start ≥0, duration >0. Unknown fields fail with field paths and spelling suggestions. Output is SMF type 1, PPQ 480, tempo/meter on track 0; drums use channel index 9, chord tracks skip 9. Compare summary to intent before claiming success.

## Limits

MIDI contains notes, not rendered audio. Key scores are heuristic correlations, not probabilities; ambiguous chords may be `?`. Scanned files are candidates, not proof of loadability or runtime plugin IDs. SoundCraft is pre-alpha; consult the reference and runtime discovery rather than inventing commands. Built-in synth has no verified LFO/unison controls. Installs and harness config edits require explicit authorization; honor consent already granted for that same scope.

## Related skills

Use `soundcraft-setup` for connection/file roots, `chords`/`drums` for composition, `plugins` for inventory/loading, `sound-design` for patches and `theory-coach` for explanations.

<!-- ideas: Korben00/ableton-producer-skills (MIT), Goldwaterfung/Stratawright (MIT); state inspection, bounded measurement and concise reporting, rewritten for SoundCraft. -->
