---
name: theory-coach
description: Analyze a supplied MIDI file for estimated or user-supplied key, chord spans, Roman numerals, and evidence-based harmonic explanations.
license: MIT
---

## When to use

Use when a user wants to understand the harmony in a MIDI file or a named MIDI track. This skill performs read-only analysis. It estimates key from note-duration pitch-class profiles and labels chord spans; it does not establish musical intent or calibrated confidence.

## Workflow

1. **Preflight.** If SoundCraft MCP is available, call `list_commands` and confirm `file.export_midi` is present before export. Its documented parameters are `{path, tracks?}`; `tracks` is a list of MIDI track names. Recheck actual parameter details with `list_commands` if the runtime schema differs. Do not invent export parameters. If unavailable, use a user-supplied `.mid` file. Do not install software or edit MCP configuration.
2. **Read state.** Inspect the supplied file path and, for export, the current session and exact named track. Export only that track when requested; analyze an unfiltered file only when the user asked for the whole file. Do not imply export or analysis succeeded until the tool or script returns success.
3. **Act.** Run commands from this skill's directory. Analyze with:

   ```powershell
   python ../soundcraft-core/scripts/analyze_midi.py "C:/path/to/song.mid" --track "Track Name" --json
   ```

   Omit `--track` for whole-file analysis. Add `--key "D minor"` only when the user supplied a key or explicitly asks to test a key hypothesis. `--window 1` is the default chord window in quarter-note beats; choose a different positive beat window only when suitable to the musical context, and disclose it. The `--key` value sets Roman numeral context; JSON `key_source` will be `supplied` while `key`/`runner_up` remain the estimator's ranking.
4. **Re-read and explain.** Check the command result and JSON. Explain the estimated key, runner-up, and their scores as Pearson correlations from a duration-weighted Krumhansl–Kessler profile heuristic, never as probabilities or calibrated confidence. If the user supplied a key, distinguish it from the estimator's ranking and explain that it supplies the Roman numeral context. Present chord symbols, beat spans, and Roman numerals proportionate to the evidence. Explain likely function, borrowed-chord possibilities, and voice-leading only when supported by the notes and context; mark interpretations as possibilities rather than facts. A `?` span stays ambiguous and must not be replaced with a guessed chord. No pitched notes means no key estimate; silence produces no chord spans, and channel 9 drums are ignored.
5. **Bounded correction.** If a result is invalid or misleading, make at most three analysis attempts, adjusting only a justified option such as exact track filter or beat window. Report each failure or warning plainly; never force a key or chord label to hide uncertainty. If the MIDI file is absent or export is unavailable, ask the user to provide a `.mid` file or report the limitation.
6. **Hand-off and report.** For reharmonization or creating/changing chords, hand off to the `chords` skill; do not edit MIDI tracks automatically. Summarize input scope, key/ranking evidence, chord and Roman numeral findings, ambiguities, options used, and any failure or warning in plain language.

Reply to the user in the language they wrote in.

## Style table

| Request | Response style |
| --- | --- |
| Key and harmony explanation | Concise evidence first, then plain-language interpretation; distinguish analyzer output from musical inference. |
| Ambiguous or sparse MIDI | State what the notes support and preserve unknown spans as `?`. |

## Spec pattern

N/A — this skill analyzes existing MIDI and does not generate a MIDI specification.

## Checks

- The analyzer accepts Standard MIDI Files, including type 0 and type 1, running status, velocity-zero note-offs, missing tempo (default 120 BPM), and overlapping same-pitch notes.
- JSON reports `key` and `runner_up` objects (`name`, `tonic`, `mode`, `score`), `key_source` (`estimated` or `supplied`), `score_kind`, and `chords` objects (`start_beat`, `end_beat`, `symbol`, `roman`).
- Check exit status: 0 is success, 2 is invalid/unreadable MIDI or analysis options, and 1 is an unexpected error. Report errors without presenting partial output as findings.
- Before any SoundCraft export, re-read the session/track state after export and confirm the returned file path exists before running the analyzer.

## Limits

- Key scores are Pearson correlations, a ranking heuristic rather than probability or calibrated confidence. A runner-up is a competing fit, not a confidence interval.
- Chord labels come from fixed beat windows and pitch-class templates. Pitches contributing under 10% of the full window are discarded; labels can miss passing tones, changing harmony inside a window, extensions, or context. Silence is `?`; sparse or unsupported pitch collections are also `?`.
- The estimator uses all selected pitched notes weighted by duration. A track filter matches the exact track name and errors if no track matches; without it, all non-drum tracks contribute. Polyphonic files can combine independent parts into misleading chords or keys.
- Tempo is read from MIDI metadata or defaults to 120 BPM, but this analysis reports beats rather than listening to timing feel. Channel 9 is excluded. Drum-only or note-free input has no estimated key and no chord spans.
- A supplied key changes Roman numeral interpretation; it does not validate that key against the MIDI. Roman numerals use the selected key's major or natural-minor scale, so modal, tonal, or enharmonic readings may need qualification. Analysis is read-only and makes no automatic track edits.

## Related skills

- `chords` — create, arrange, or reharmonize chord progressions.
- `soundcraft-core` — MIDI analysis command and shared SoundCraft command reference.

<!-- ideas: Original workflow and interpretations written for this repository; no external text adapted. -->
