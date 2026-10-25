# SoundCraft Skills — Phase 1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship a cross-harness (Claude Code / Codex / Antigravity) Agent Skills plugin with 8 skills that turn producer requests into chords, drums, sounds, plugin choices and theory analysis inside the SoundCraft DAW, with a `.mid` fallback.

**Architecture:** One canonical `skills/` tree. All code lives in `skills/soundcraft-core/scripts/` (stdlib-only Python package `scmidi` + CLIs). Agents write a JSON spec → `make_midi.py` renders `.mid` + a text summary → SoundCraft MCP `file.import_midi`. Other skills call core scripts by the relative path `../soundcraft-core/scripts/...`. Per-harness manifests at the repo root; `install.py` is the fallback installer.

**Tech Stack:** Python ≥3.9 stdlib only (`unittest`, `struct`, `json`, `random`, `difflib`, `pathlib`), Markdown skills (Agent Skills spec), SoundCraft MCP (`soundcraft-cli mcp`).

**Spec:** `docs/superpowers/specs/2026-10-25-soundcraft-skills-design.md`. Read §4, §4.5 and §5 before any task.

## Model assignment (cost plan, spec §9)

Every task header has a **Model** line. The orchestrator dispatches each implementer on that model. Reviews run on the main model (Opus).
- **opus**: core algorithms where a subtle bug produces wrong music.
- **sonnet**: research, CLIs, skill prose, knowledge files.
- **haiku**: mechanical docs.
- Knowledge-file tasks can go to GPT via T3 `delegate_task` instead of Sonnet if the user prefers.

## Global Constraints

- Python ≥3.9, **stdlib only**, no third-party imports anywhere (tests included).
- All code under `skills/soundcraft-core/scripts/`. Tests under `tests/`. Run all tests with `python -m unittest discover -s tests -t .` from the repo root.
- `tests/__init__.py` inserts `skills/soundcraft-core/scripts` into `sys.path`, so tests `import scmidi`.
- SMF type 1, PPQ 480. Tempo and time signature go in track 0. Drums use MIDI channel index 9 (channel 10). Chord tracks use channel indexes 0, 1, 2…, skipping 9.
- Middle C = `C4` = MIDI 60.
- Step characters: `x` = 100, `X` = 120, `g` = 45, `.` = rest.
- `make_midi.py` exit codes: 0 = OK, 2 = invalid spec (message names field path + bad value + accepted values), 1 = unexpected/IO error.
- Nothing is written unless validation passes: pitch 0–127, velocity 1–127, start ≥ 0, duration > 0.
- SKILL.md frontmatter has only spec fields (`name`, `description`, optional `license`, `metadata`). `name` = folder name, matches `^[a-z0-9]+(-[a-z0-9]+)*$`, ≤64 chars. `description` ≤1024 chars.
- Every SKILL.md has these H2 sections in order: `When to use`, `Workflow`, `Style table`, `Spec pattern`, `Checks`, `Limits`, `Related skills`. `Style table` and `Spec pattern` may say "N/A — <reason>".
- User-facing skill prose is Thai with English technical terms. Code, identifiers and comments are English.
- Never auto-download or run plugin installers. Any system change (install software, edit harness config) needs explicit user confirmation, written into the skill workflow.
- License MIT, "Copyright (c) 2026 Chaiyaporn Santangjai" (`LICENSE` already exists). Write all content in our own words. Credits go in `CREDITS.md`.
- Commit after every task with a message ending in `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.

## Review Focus

1. **Typo'd spec fields** (`"voiceing": "open"`): if silently ignored, the user gets wrong music with no clue why. Expect exit 2 with `unknown field 'voiceing' (did you mean 'voicing'?)`. Tested in Task 6.
2. **Chord spelling variants users really type**: `C♯m7`, `B♭maj7`, `CΔ7`, `C-7`, `Cmin7`, `C°7`, `Cø7`, `CM7`, lowercase root `am7`. Expect each to parse the same as its canonical form. Tested in Task 3.
3. **MIDI files from other DAWs** in theory-coach: type 0, running status, note-on with velocity 0 used as note-off, a missing tempo event (default 120 BPM), overlapping same-pitch notes. Expect them to parse. Tested in Task 2.
4. **Non-ASCII and space-containing paths** (Thai Windows usernames, `C:\Users\ชัยพร\My Music\ไฟล์.mid`, plugin names with spaces or accents). Expect writing, scanning and reporting to work. Tested in Tasks 6 and 8.
5. **Long progressions drifting out of range** under voice leading, e.g. 32 chords of a ii–V–I cycle through all keys. Expect every voiced note (bass excluded) to stay within `range`. Tested in Task 4.

---

### Task 1: Verify SoundCraft command surface

**Model:** sonnet

**Files:**
- Create: `skills/soundcraft-core/references/soundcraft-commands.md`

**Interfaces:**
- Produces:
  - The facts every skill and Task 5's `SOUNDCRAFT_MAP` depend on.
  - A final line `drum_synth map: GM` or `drum_synth map: CUSTOM` followed by a `voice → note` table.
  - A line `mcp args: ["mcp"]` (or the verified args) used by `.mcp.json` and `install.py`.

- [ ] **Step 1: Research.** Read https://github.com/storytold/soundcraft with WebFetch only (no cloning, no executing). Use `api.github.com/repos/storytold/soundcraft/git/trees/HEAD?recursive=1`, then raw files: `docs/mcp.md`, `docs/control-protocol.md`, `docs/plugin-parity.md`, `AGENTS.md`, and the `crates/engine/src/cmd/*` command modules.
- [ ] **Step 2: Write the reference file** with these H2 sections. For each command record the id, params JSON, an example and the source path. Mark anything not found as `UNVERIFIED (looked in: …)`.
  - `MCP server` — launch args. Say whether `--demo` is required. Cover `--automation-read-root` and `--automation-write-root`.
  - `MCP tools` — `list_commands`, `execute`, `batch`, `inspect_session`, `new_session`, `open_session`, `save_session`, `import_audio`, `bounce_mix`.
  - `Commands we use` — `track.new`, `file.import_midi`, `file.export_midi`, `mix.instrument`, `mix.insert`, `mix.volume`, the third-party plugin load command, plugin rescan (if any), preset save/load, set plugin parameter, read plugin parameter ranges, transport stop.
  - `Built-in plugins` — all 25 ids with category.
  - `subtractive_synth parameters` — name, range, unit.
  - `drum_synth` — MIDI note → voice map.
  - `Plugin folders` — what SoundCraft scans per OS.
  - `Error recovery` — the three-class table from spec §4.5-E, filled with real error strings where found.
  - `Known limits` — sandbox, in-process crash, signed macOS VST3, no sidechain, no live MIDI.
- [ ] **Step 3: Verify.** Every command in "Commands we use" has a source path or an UNVERIFIED mark, and the file ends with the `drum_synth map:` line and the `mcp args:` line.
- [ ] **Step 4: Commit** `docs(core): verified soundcraft command reference`

---

### Task 2: MIDI data model, writer and reader

**Model:** opus

**Files:**
- Create: `tests/__init__.py`, `.gitignore` (`__pycache__/`, `*.pyc`, `/out/`)
- Create: `skills/soundcraft-core/scripts/scmidi/__init__.py`, `scmidi/model.py`, `scmidi/midi_writer.py`, `scmidi/midi_reader.py`
- Test: `tests/test_midi_io.py`

**Interfaces:**
- Produces, in `scmidi.model`:
  - `@dataclass(frozen=True) Note(pitch: int, start: int, duration: int, velocity: int, channel: int)`. Times are in ticks.
  - `@dataclass Track(name: str, channel: int, notes: list[Note])`
  - `@dataclass Song(bpm: float, time_signature: tuple[int, int], tracks: list[Track], ppq: int = 480)`
  - `class MidiError(ValueError)`
- Produces, in `scmidi.midi_writer`: `encode_smf(song: Song) -> bytes` and `write_smf(song: Song, path: str | Path) -> None`. Creates parent dirs. Raises `MidiError` if any note violates the Global Constraints ranges.
- Produces, in `scmidi.midi_reader`: `decode_smf(data: bytes) -> Song` and `read_smf(path) -> Song`.
  - Type 0 and type 1.
  - Running status.
  - Note-on with velocity 0 counts as note-off.
  - First tempo wins; default 120 if there is none.
  - Default time signature (4, 4).
  - Track name from meta 0x03.
  - Notes are grouped per (track, channel). A type 0 file is split by channel.
  - Unmatched note-ons end at the end of the track.

- [ ] **Step 1: Write the failing tests** in `tests/test_midi_io.py`:
  - `test_roundtrip_notes_tempo_timesig` — a Song with bpm 90, (3, 4), and one track of 3 notes → `decode_smf(encode_smf(s))` equals bpm 90.0 (±0.01), (3, 4) and the same notes.
  - `test_header_is_type1_ppq480` — bytes start with `b"MThd\x00\x00\x00\x06\x00\x01"` and ppq bytes `\x01\xe0`.
  - `test_track0_is_conductor` — a song with 2 tracks → header ntrks == 3.
  - `test_invalid_velocity_raises` — velocity 0 → `MidiError`. Pitch 128 → `MidiError`.
  - `test_reads_type0_running_status_vel0_off` — a hand-built type 0 byte string, channels 0 and 9, running status, vel-0 note-offs → 2 tracks with the correct notes.
  - `test_missing_tempo_defaults_120`.
  - `test_overlapping_same_pitch` — two overlapping note-ons on pitch 60 then two offs → 2 notes. Pair FIFO.
  - `test_unicode_path_with_spaces` — `write_smf` / `read_smf` to `tmp/โฟลเดอร์ เพลง/ไฟล์ ทดสอบ.mid`.
- [ ] **Step 2: Run** `python -m unittest tests.test_midi_io -v`. Expect FAIL (ImportError).
- [ ] **Step 3: Implement.**
  - The writer uses VLQ delta times and emits note-off events as 0x80.
  - Events at the same tick are sorted with offs before ons.
  - The tempo meta is `FF 51 03`, using `round(60_000_000 / bpm)`.
  - The time-signature meta is `FF 58 04 nn dd(log2) 24 8`.
  - Track names use `FF 03`.
- [ ] **Step 4: Run.** Expect all PASS.
- [ ] **Step 5: Commit** `feat(core): SMF writer/reader with data model`

---

### Task 3: Chord, key and roman-numeral parsing

**Model:** opus

**Files:**
- Create: `skills/soundcraft-core/scripts/scmidi/theory.py`
- Test: `tests/test_theory_parse.py`

**Interfaces:**
- Produces, in `scmidi.theory`:
  - `class TheoryError(ValueError)`
  - `parse_note(name: str) -> int` — pitch class 0–11. Accepts `C C# Db … B`, `♯ ♭`, and a lowercase root.
  - `pitch_name(midi: int) -> str` — `60 → "C4"`, `61 → "C#4"`. Uses sharps.
  - `@dataclass(frozen=True) Chord(root: int, intervals: tuple[int, ...], bass: int | None, symbol: str)`. `intervals` are semitones above the root, sorted, and include 0.
  - `parse_chord(symbol: str) -> Chord`
  - `@dataclass(frozen=True) Key(tonic: int, mode: str)`, where mode is `"major"` or `"minor"`.
  - `parse_key(text: str) -> Key` — accepts `"D minor"`, `"Dm"`, `"D min"`, `"F# major"`, `"C"`, `"Bb"`.
  - `parse_roman(numeral: str, key: Key) -> Chord`
  - `parse_chord_token(token: str, key: Key | None) -> Chord` — tries roman numerals first if a key is set and the token matches the roman regex, otherwise a chord symbol.
  - `QUALITIES: dict[str, tuple[int, ...]]` — exported for Task 7.

- [ ] **Step 1: Write the failing tests:**
  - `test_qualities` — table-driven over every quality in spec §4:

    | Symbol | Intervals |
    |---|---|
    | `C` | (0, 4, 7) |
    | `Cm` | (0, 3, 7) |
    | `Cdim` | (0, 3, 6) |
    | `Caug` | (0, 4, 8) |
    | `Csus2` | (0, 2, 7) |
    | `Csus4` | (0, 5, 7) |
    | `C5` | (0, 7) |
    | `C6` | (0, 4, 7, 9) |
    | `Cm6` | (0, 3, 7, 9) |
    | `C7` | (0, 4, 7, 10) |
    | `Cmaj7` | (0, 4, 7, 11) |
    | `Cm7` | (0, 3, 7, 10) |
    | `CmMaj7` | (0, 3, 7, 11) |
    | `Cm7b5` | (0, 3, 6, 10) |
    | `Cdim7` | (0, 3, 6, 9) |
    | `C9` | (0, 4, 7, 10, 14) |
    | `Cmaj9` | (0, 4, 7, 11, 14) |
    | `Cm9` | (0, 3, 7, 10, 14) |
    | `C11` | (0, 4, 7, 10, 14, 17) |
    | `Cm11` | (0, 3, 7, 10, 14, 17) |
    | `C13` | (0, 4, 7, 10, 14, 21) |
    | `Cmaj13` | (0, 4, 7, 11, 14, 21) |
    | `Cadd9` | (0, 4, 7, 14) |
    | `Cadd11` | (0, 4, 7, 17) |

  - `test_alterations` — `C7b9` → (0, 4, 7, 10, 13). `C7#9` → (0, 4, 7, 10, 15). `Cmaj7#11` → (0, 4, 7, 11, 18). `C7b13` → (0, 4, 7, 10, 20). `C7b5` → (0, 4, 6, 10). `C7#5` → (0, 4, 8, 10).
  - `test_slash` — `G/B` → root 7, bass 11.
  - `test_aliases` — each pair parses to equal (root, intervals, bass):
    - `C♯m7`=`C#m7`
    - `B♭maj7`=`Bbmaj7`
    - `CΔ7`=`Cmaj7`
    - `CM7`=`Cmaj7`
    - `C-7`=`Cm7`
    - `Cmin7`=`Cm7`
    - `C°7`=`Cdim7`
    - `Cø7`=`Cm7b5`
    - `am7`=`Am7`
  - `test_bad_chord_message` — `parse_chord("Xm7")` raises `TheoryError` whose message contains `"Xm7"` and `"root"`. `parse_chord("Cblah")` mentions `"quality"`.
  - `test_keys` — `parse_key("D minor") == Key(2, "minor")`. `"Dm"`, `"D min"` are the same. `"Bb"` == `Key(10, "major")`.
  - `test_roman_minor` — key D minor: `i, VI, III, VII` → roots 2, 10, 5, 0 with qualities m, maj, maj, maj.
  - `test_roman_major_sevenths` — key C: `ii7` → D m7. `V7` → G 7. `Imaj7` → C maj7. `bVII` → Bb major. `V/V` → D major. `viiø7` → B m7b5.
  - `test_pitch_name` — `pitch_name(60) == "C4"`, `pitch_name(21) == "A0"`.
- [ ] **Step 2: Run** `python -m unittest tests.test_theory_parse -v`. Expect FAIL.
- [ ] **Step 3: Implement.**
  - Normalise aliases first: `♯→#`, `♭→b`, `Δ→maj`, `M7→maj7`, `min→m`, `-→m` when directly after the root, `°→dim`, `ø→m7b5`.
  - Then match the regex `^([A-Ga-g][#b]?)(quality)?((?:[b#](?:5|9|11|13))*)(?:/([A-Ga-g][#b]?))?$`.
  - Alterations add or replace intervals: `b5`/`#5` replace 7. `b9`/`#9` add 13/15. `#11` adds 18. `b13` adds 20.
  - Roman numerals: case gives the quality (upper = major, lower = minor). Suffixes are `°`/`dim`, `ø`, `+`, `7`, `maj7`, `9`, and accidentals `b`/`#` go before the numeral. Degrees come from the major scale `[0,2,4,5,7,9,11]`, or natural minor `[0,2,3,5,7,8,10]` for a minor key. `X/Y` = chord X built on degree Y of the key.
- [ ] **Step 4: Run.** Expect PASS.
- [ ] **Step 5: Commit** `feat(core): chord/key/roman parsing`

---

### Task 4: Voicing and voice leading

**Model:** opus

**Files:**
- Modify: `skills/soundcraft-core/scripts/scmidi/theory.py`
- Test: `tests/test_voicing.py`

**Interfaces:**
- Consumes: `Chord` and `parse_chord` (Task 3).
- Produces: `voice_chord(chord: Chord, voicing: str, octave: int, range_: tuple[int, int], previous: list[int] | None = None, voice_leading: bool = True, bass_note: bool = False) -> tuple[list[int], int | None]`. Returns (sorted upper-structure pitches, bass pitch or None). `voicing` is one of `close | open | drop2 | spread | rootless`. Raises `TheoryError` on an unknown voicing.

**Algorithm** (the signature leaves these choices open, so they are fixed here):
1. Base pitch of the root = `12 * (octave + 1) + chord.root`.
2. `close` — stack the intervals ascending from the base.
3. `open` — close, then raise the second-lowest note by 12.
4. `drop2` — close (needs ≥4 notes, otherwise behaves as close), then lower the second-highest note by 12.
5. `spread` — root at base−12. Each next tone in interval order goes at the lowest pitch with that pitch class that is ≥ previous + 5.
6. `rootless` — drop interval 0 if the chord has ≥4 tones. Close-stack the rest from the base. When the caller passed the default range (48, 79), use (56, 74) instead.
7. Fit to range — shift the whole voicing by ±12 to minimise notes outside the range. Then fold each remaining outlier by ±12 until it is inside. Dedupe and sort.
8. Voice leading (if `previous` and `voice_leading`) — the candidates are every rotation of the step-6 voicing (move the lowest note up 12, n−1 times) × shifts {−12, 0, +12}, each fitted per step 7. Cost = Σ over the candidate's notes of the min |note − p| for p in `previous`. Ties go to the candidate whose mean pitch is closest to the range centre.
9. Bass — if `chord.bass is not None` or `bass_note`, the bass pc = `chord.bass` if it is set, else root. The bass pitch is the highest pitch with that pc that is ≤ min(voicing) − 5. The bass is not range-constrained and not part of voice leading.

- [ ] **Step 1: Write the failing tests:**
  - `test_close_c_major_oct4` → ([60, 64, 67], None).
  - `test_open` — Cmaj7 open → [60, 67, 71, 76].
  - `test_drop2` — Cmaj7 drop2 oct 4 → [55, 60, 64, 71]. Range (48, 79).
  - `test_rootless_dm9` — Dm9 rootless → every note in 56–74, and pc 2 is not in the set.
  - `test_slash_bass` — G/B → bass pc 11, bass ≤ min(upper) − 5.
  - `test_voice_leading_small_motion` — C → F with previous [60, 64, 67] → [60, 65, 69].
  - `test_voice_leading_off_keeps_root_position` — F, voice_leading=False → [65, 69, 72].
  - `test_long_cycle_stays_in_range` — 32 chords of ii7–V7–Imaj7 through all 12 keys, chained → every upper note in [48, 79].
  - `test_narrow_range_folds` — C13 with range (60, 72) → every note in [60, 72], no duplicates.
  - `test_unknown_voicing` → `TheoryError` mentioning `"voicing"` and listing the accepted values.
- [ ] **Step 2: Run** `python -m unittest tests.test_voicing -v`. Expect FAIL.
- [ ] **Step 3: Implement** per the algorithm above.
- [ ] **Step 4: Run** the full suite. Expect PASS.
- [ ] **Step 5: Commit** `feat(core): voicings and voice leading`

---

### Task 5: Rhythm and drum maps

**Model:** opus

**Files:**
- Create: `skills/soundcraft-core/scripts/scmidi/rhythm.py`, `scmidi/drums.py`
- Test: `tests/test_rhythm_drums.py`

**Interfaces:**
- Consumes: `Note` (Task 2) and Task 1's `drum_synth map` line.
- Produces, in `scmidi.rhythm`:
  - `STEP_VELOCITY = {"x": 100, "X": 120, "g": 45}`
  - `parse_steps(pattern: str, steps_per_bar: int) -> list[str]` — validates the chars `xXg.` and that len % steps_per_bar == 0. Spaces and `|` are ignored. The `TheoryError`-style `ValueError` message gives the 1-based position of a bad char.
  - `step_tick(index: int, steps_per_bar: int, beats_per_bar: float, ppq: int, swing: float) -> int` — the step length is d = beats_per_bar × ppq / steps_per_bar. Odd steps are delayed by `round((2*swing - 1) * d)`.
  - `ms_to_ticks(ms: float, bpm: float, ppq: int) -> int`
  - `humanize(notes: list[Note], amount: float, ppq: int, seed: int) -> list[Note]` — timing jitter is uniform in ±`round(amount * ppq * 0.05)`, velocity jitter is ±`round(amount * 12)`. It clamps start ≥ 0 and velocity 1–127, uses `random.Random(seed)`, and amount 0 returns an equal list.
  - `chord_hits(rhythm: str, length_ticks: int, ppq: int, beats_per_bar: float, custom_steps: list[str] | None) -> list[tuple[int, int, int | None, float]]` — returns (rel_start, duration, note_index or None = all notes, velocity_scale). The rhythms:
    - `pad` — one hit for the full length.
    - `block` — a hit every beat, duration `round(0.9 * ppq)`.
    - `stabs` — hits at beat 0 and beat 2 (if inside the length), duration ppq // 2.
    - `arp-up`/`arp-down`/`arp-updown` — 16ths (ppq // 4) cycling the note indexes. `updown` does not repeat the endpoints.
    - `custom` — the 16-step bar pattern repeated. Each hit lasts until the next non-rest or the chord end. The velocity scale is `STEP_VELOCITY[c] / 100`.
- Produces, in `scmidi.drums`:
  - `VOICES` — the tuple of 16 names from spec §4.
  - `GM_MAP` — kick 36, snare 38, clap 39, rim 37, hat 42, open_hat 46, pedal_hat 44, ride 51, crash 49, tom_hi 50, tom_mid 47, tom_low 45, shaker 70, tambourine 54, cowbell 56, perc 75.
  - `SOUNDCRAFT_MAP` — from Task 1; equal to `GM_MAP` if Task 1 says GM.
  - `resolve_drum_map(value: str | dict) -> dict[str, int]` — `"gm"`, `"soundcraft"`, or a dict merged over GM. An unknown voice or a note outside 0–127 raises `ValueError` naming the voice.

- [ ] **Step 1: Write the failing tests:**
  - `test_parse_steps_ok_and_bad_char` — `"x...x..."` with 8 steps is OK. `"x..q"` gives an error containing `"position 4"`.
  - `test_parse_steps_ignores_bar_separators` — `"x... | x..."` with 4 steps → 8 steps.
  - `test_swing` — 16 steps, 4/4, ppq 480, swing 0.5 → step 1 at 120. Swing 0.75 → step 1 at 180. Step 2 stays at 240.
  - `test_ms_to_ticks` — 25 ms at 120 BPM, ppq 480 → 24.
  - `test_humanize_deterministic_and_clamped` — same seed gives equal output, a different seed differs, and amount 0 returns the identity.
  - `test_chord_hits_each_rhythm` — the counts for 1 bar 4/4: pad 1, block 4, stabs 2, arp-up 16 (indexes 0, 1, 2, 0…), arp-updown on 3 notes cycles 0, 1, 2, 1, 0, 1….
  - `test_drum_maps` — `resolve_drum_map("gm")["kick"] == 36`. A custom `{"kick": 24}` → kick 24, snare 38. `{"cowbel": 56}` → `ValueError` containing `"cowbel"`.
- [ ] **Step 2: Run** `python -m unittest tests.test_rhythm_drums -v`. Expect FAIL.
- [ ] **Step 3: Implement.**
- [ ] **Step 4: Run.** Expect PASS.
- [ ] **Step 5: Commit** `feat(core): rhythm, swing, humanize, drum maps`

---

### Task 6: Spec validation, rendering and the `make_midi.py` CLI

**Model:** opus

**Files:**
- Create: `skills/soundcraft-core/scripts/scmidi/spec.py`, `scmidi/render.py`, `skills/soundcraft-core/scripts/make_midi.py`
- Create: `skills/soundcraft-core/examples/lofi-sketch.json` (the spec §4 example, verbatim)
- Test: `tests/test_spec.py`, `tests/test_make_midi_cli.py`

**Interfaces:**
- Consumes: Tasks 2–5.
- Produces, in `scmidi.spec`:
  - `class SpecError(ValueError)` with attributes `path: str` (e.g. `"tracks[1].pattern.kick"`) and `message`. `str(e)` = `f"{path}: {message}"`.
  - `validate_spec(raw: dict) -> dict` — returns a normalised copy with defaults applied.
- Produces, in `scmidi.render`: `render(spec: dict) -> tuple[Song, list[str]]` — takes an already-validated spec and returns the Song and summary lines.
- Produces the CLI: `python make_midi.py SPEC.json [--out PATH] [--json]`.
  - `SPEC.json` may be `-` for stdin.
  - `--out` overrides the spec's `output`. The default output is `<spec stem>.mid` next to the spec.
  - Prints the summary lines, then `Wrote: <abs path>`.
  - `--json` prints `{"output": path, "tracks": [{"name", "bars": [{"bar": n, "chord": sym, "notes": ["D3", …]}]}]}` instead. Drum tracks list `{"bar": n, "hits": {"kick": 4, …}}`.

**Defaults and limits** (copy into `validate_spec`):
- Top level:
  - `bpm` 120, range 20–300.
  - `time_signature` [4, 4]: numerator 1–16, denominator in {2, 4, 8, 16}.
  - `key` null.
  - `output` `"out.mid"`.
  - `tracks` is required and non-empty, with at most 16 tracks.
- Chord tracks:
  - `progression` is required. It is a list of strings, a list of objects `{chord, beats|bars}`, or a single string split on `-` or `|`.
  - `chord_length`: `"1bar"`, `"Nbars"`, `"Nbeats"` or a number of beats. Default `"1bar"`.
  - `voicing` `"close"`.
  - `octave` 4, range 1–7.
  - `range` [48, 79]: low < high, high − low ≥ 12, both in 0–127.
  - `rhythm` `"pad"`. `steps` is required iff the rhythm is `custom`.
  - `velocity` 90, range 1–127.
  - `humanize` 0, range 0–1.
  - `seed` 1.
  - `repeat` 1, range 1–64.
  - `voice_leading` true.
  - `bass_note` false.
  - `strum_ms` 0, range 0–100.
- Drum tracks:
  - `pattern` is required and non-empty, keyed by `VOICES`.
  - `steps` 16, one of 4, 8, 12, 16, 24, 32.
  - `swing` 0.5, range 0.5–0.75.
  - `bars` 4, range 1–256.
  - `humanize` 0.
  - `seed` 1.
  - `offset_ms` {}, values −50 to 50.
  - `velocity` {}, per-voice overrides of `x`/`X`/`g`, 1–127.
  - `fill` null, or `{every: 1–64, pattern: {voice: steps}}`.
  - `drum_map` `"gm"`.
- Any unknown key at any level → `SpecError` with a `difflib.get_close_matches` suggestion: `unknown field 'voiceing' (did you mean 'voicing'?)`.
- A `type` other than `chords`/`drums` → an error listing both.

**Render rules:**
- Bar ticks = `round(num * 4 / den * ppq)`.
- Chord track: the progression × `repeat` is laid end to end. Each chord's notes come from `voice_chord`, chaining `previous` per chord. `chord_hits` is applied per chord. Strum offsets note i (low → high) by `i * ms_to_ticks(strum_ms)`, clipped so that duration stays ≥ 1. Humanize comes last.
- Drum track: the pattern repeats to fill `bars`. A voice pattern longer than one bar cycles. A fill replaces, for the listed voices only, bar k where `(k + 1) % every == 0`. Each hit lasts one step (min 1 tick), with `offset_ms` and velocity overrides applied, then swing, then humanize. A negative start clamps to 0.
- Summary line for chords: `Bar {n}: {symbol} = {pitch names low→high incl. bass}`. One line per chord start, using the bar where the chord starts. For drums: `Bar {n}: kick×4 snare×2 hat×8`.
- Validate every note (Global Constraints) before returning. A violation raises `SpecError(path="tracks[i]", …)`.

- [ ] **Step 1: Write the failing tests** in `tests/test_spec.py`:
  - `test_example_spec_validates_and_renders` — the example file → 2 tracks + conductor. The first summary line starts with `"Bar 1: Dm9 = "`.
  - `test_defaults_applied` — `{"tracks": [{"type": "chords", "progression": "C - G - Am - F"}]}` → 4 chords, bpm 120, 4 bars of notes.
  - `test_unknown_field_suggestion` — the `"voiceing"` case. The message contains `"did you mean 'voicing'"`, and the path is `"tracks[0].voiceing"`.
  - `test_bad_chord_path` — progression `["C", "Xm7"]` → path `"tracks[0].progression[1]"`.
  - `test_roman_requires_key` — `"i - VI"` without a key → the message mentions `"key"`.
  - `test_range_too_narrow` — range [60, 65] → a `SpecError` on `range`.
  - `test_drum_fill_every_4` — 8 bars, fill every 4 → bars 4 and 8 use the fill snare; the kick is unchanged in bar 4.
  - `test_offset_and_velocity_overrides` — snare `offset_ms` 25 at 120 BPM → snare start +24 ticks. Hat `x` override 85 → velocity 85.
  - `test_chord_lengths` — `{"chord": "G/B", "beats": 2}` occupies 960 ticks. `chord_length` `"2bars"` → 3840.
  - `test_strum` — `strum_ms` 15 → note starts are strictly increasing within a chord.
  - `test_channels` — two chord tracks + drums → channels 0, 1, 9.
- [ ] **Step 2: Write the failing tests** in `tests/test_make_midi_cli.py` (via `subprocess.run([sys.executable, script, …])`):
  - `test_cli_writes_and_prints_summary` — exit 0, stdout contains `"Wrote: "`, and the file is readable by `read_smf`.
  - `test_cli_invalid_exit2` — a bad spec → exit 2, stderr contains the field path, and no output file is created.
  - `test_cli_json_output` — `--json` → parseable, with an `output` key.
  - `test_cli_stdin_and_unicode_out` — spec on stdin with `--out "<tmp>/เพลง ใหม่/ทดสอบ.mid"` → exit 0, file exists. Set `PYTHONIOENCODING=utf-8` in the env, and the script itself reconfigures stdout to UTF-8.
- [ ] **Step 3: Run both test modules.** Expect FAIL.
- [ ] **Step 4: Implement** `spec.py`, `render.py` and `make_midi.py`. The CLI catches `SpecError` → stderr + exit 2, and `OSError` → stderr + exit 1.
- [ ] **Step 5: Run** the full suite. Expect PASS.
- [ ] **Step 6: Commit** `feat(core): JSON spec validation, renderer, make_midi CLI`

---

### Task 7: MIDI analysis and the `analyze_midi.py` CLI

**Model:** opus

**Files:**
- Create: `skills/soundcraft-core/scripts/scmidi/analysis.py`, `skills/soundcraft-core/scripts/analyze_midi.py`
- Test: `tests/test_analysis.py`

**Interfaces:**
- Consumes: `read_smf` and `Song` (Task 2), `QUALITIES`, `Key` and `parse_chord` (Task 3), `render` (Task 6, test fixtures only).
- Produces, in `scmidi.analysis`:
  - `@dataclass KeyGuess(key: Key, score: float)`
  - `estimate_key(notes: list[Note]) -> list[KeyGuess]` — all 24 keys sorted by descending score. Krumhansl–Kessler major/minor profiles, pitch classes weighted by duration, Pearson correlation.
  - `name_chord(pitches: list[int]) -> tuple[str, float]` — symbol and score, `"?"` if there are fewer than 2 distinct pitch classes or the score < 0.5. Template match over `QUALITIES` (excluding the 11/13 extensions) for each candidate root among the present pitch classes. Score = (matched − 0.5 × extra − missing) / len(template). A tie goes to root = lowest pitch, then fewer tones. A slash is added when the lowest pitch's pc ≠ root and is a chord tone or extra.
  - `to_roman(symbol: str, key: Key) -> str` — `"?"` stays `"?"`. Non-diatonic roots get `b`/`#` (e.g. Bb in C → `bVII`).
  - `@dataclass ChordSpan(start_beat: float, end_beat: float, symbol: str, roman: str)`
  - `detect_chords(song: Song, window_beats: float = 1.0, key: Key | None = None) -> list[ChordSpan]` — skips channel 9. Pitches sounding in each window are weighted by overlap; pitches below 10% of the window are dropped. Adjacent identical symbols are merged.
- Produces the CLI: `python analyze_midi.py FILE.mid [--window BEATS] [--track NAME] [--key "D minor"] [--json]`.
  - Text output: `Key: D minor (0.87) — runner-up: F major (0.81)`, then `Bar 1 beat 1: Dm9 (i9)` lines.
  - Exit 2 on an unreadable or invalid MIDI file.

- [ ] **Step 1: Write the failing tests:**
  - `test_key_c_major_scale` — C major scale notes → top guess `Key(0, "major")`.
  - `test_key_from_rendered_dm_progression` — render `Dm - Gm - A7 - Dm` in D minor → top guess `Key(2, "minor")`.
  - `test_name_chord` — [60, 64, 67] → `"C"`. [57, 60, 64, 67] → `"Am7"`. [59, 62, 67] → `"G/B"`. [60] → `"?"`.
  - `test_to_roman` — `Bb` in C → `"bVII"`. `Dm7` in C → `"ii7"`. `A7` in D minor → `"V7"`.
  - `test_detect_roundtrip` — render `C - G - Am - F` (pad, 1 bar each), write, read and detect → symbols [C, G, Am, F] (bass and slash ignored by comparing the root+quality prefix).
  - `test_cli_ignores_drums_and_bad_file_exit2`.
- [ ] **Step 2: Run.** Expect FAIL.
- [ ] **Step 3: Implement.** Profiles:
  - major `[6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88]`
  - minor `[6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17]`
- [ ] **Step 4: Run** the full suite. Expect PASS.
- [ ] **Step 5: Commit** `feat(core): key/chord analysis and analyze_midi CLI`

---

### Task 8: Plugin scanner and user corpus

**Model:** sonnet

**Files:**
- Create: `skills/soundcraft-core/scripts/scan_plugins.py`
- Test: `tests/test_scan_plugins.py`

**Interfaces:**
- Produces:
  - `default_dirs(platform: str, env: Mapping[str, str], home: Path) -> list[tuple[Path, str]]` — returns (dir, format). The folders are exactly the per-OS list in spec §5 "plugins: โฟลเดอร์ที่สแกน", plus the CLAP_PATH entries (split on `os.pathsep`). Windows legacy VST2 dirs (`%ProgramFiles%\VSTPlugins`, `%ProgramFiles%\Steinberg\VstPlugins`, `%CommonProgramFiles%\VST2`) are added with the format `"vst2"`, for warnings only.
  - `scan(dirs: list[tuple[Path, str]]) -> dict` with:
    - `plugins`: `[{name, format, path, category}]` sorted by name.
    - `unsupported`: `[{name, format, path, reason}]`.
    - `missing_dirs`: `[str]`.
  - Recognised plugin files: `*.vst3` → VST3, `*.clap` → CLAP, `*.component` → AU. A matching bundle directory is one plugin; do not descend into it. Unsupported: `.dll` under vst2 dirs, `.vst`, `.aaxplugin`, `.lv2`.
  - `categorize(name: str) -> str` — case-insensitive keywords, first match wins, in this order:
    1. drum: drum, kit, sitala, 808, perc
    2. synth: synth, vital, surge, dexed, serum, ob-x, odin, helm, tyrell
    3. eq: eq, nova
    4. comp: comp, limit, glue
    5. reverb: reverb, verb, supermassive, room, plate
    6. delay: delay, echo
    7. saturation: satur, distort, tape, drive
    8. otherwise `other`
  - CLI: `python scan_plugins.py [--extra-dir DIR]… [--json] [--write-corpus [PATH]]`. The default corpus path is `~/.soundcraft-skills/plugins.json`, written as `{"scanned_at": ISO8601, "platform": ..., **scan_result}`. Text output groups plugins by category and prints warnings for unsupported formats with the reason `"SoundCraft supports CLAP, VST3, AU only"`.

- [ ] **Step 1: Write the failing tests** (fake trees in `tempfile.TemporaryDirectory`):
  - `test_default_dirs_windows` — a fake env (`CommonProgramFiles`, `LOCALAPPDATA`, `ProgramFiles`) → contains `<Common>\VST3` (vst3) and `<Common>\CLAP` (clap).
  - `test_default_dirs_linux_clap_path` — `CLAP_PATH="/a:/b"` with platform `"linux"` → includes `/a` and `/b`.
  - `test_scan_finds_bundles_without_descending` — `Vital.vst3/Contents/x86_64-win/Vital.vst3` (a nested file) → exactly one Vital entry.
  - `test_unsupported_reported` — `Old.dll` in a vst2 dir and `X.lv2` → both appear in `unsupported`.
  - `test_missing_dirs` — a nonexistent dir is listed and is not an error.
  - `test_unicode_and_spaces` — `Valhalla Supermassive.vst3` and `Sérum ไทย.clap` → names preserved, categories `reverb` and `synth`.
  - `test_write_corpus` — the CLI with `--extra-dir <tmp> --write-corpus <tmp>/c.json` → the JSON has `plugins` and `scanned_at`.
- [ ] **Step 2: Run.** Expect FAIL.
- [ ] **Step 3: Implement.**
- [ ] **Step 4: Run.** Expect PASS.
- [ ] **Step 5: Commit** `feat(core): plugin scanner and user corpus`

---

### Task 9: Harness manifests and `install.py`

**Model:** sonnet

**Files:**
- Create: `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`, `.mcp.json`, `.codex-plugin/plugin.json`, `.agents/plugins/marketplace.json`, `plugin.json`, `mcp_config.json`, `install.py`
- Test: `tests/test_install.py`, `tests/test_manifests.py`

**Interfaces:**
- Consumes: the Task 1 `mcp args:` line.
- Produces:
  - Plugin name `soundcraft-skills`, version `0.1.0`, author `Chaiyaporn Santangjai`, license `MIT`.
  - MCP server key `soundcraft`, command `soundcraft-cli`, args = the Task 1 value.
  - `install.py`:
    - `MCP_SERVER = {"command": "soundcraft-cli", "args": [...]}`, the single source of truth that tests compare every manifest against.
    - `install(targets: list[str], home: Path, repo: Path, dry_run: bool = False, link: bool = False) -> list[str]`. `targets` ⊆ `{"codex", "antigravity"}`. Returns human-readable action lines.
    - CLI: `python install.py [--codex] [--antigravity] [--all] [--dry-run] [--link]`. With no target it prints help. For Claude Code it prints the `/plugin marketplace add` instructions only.

- [ ] **Step 1: Verify the schemas.** Use WebFetch on the official docs: code.claude.com plugins-reference + plugin-marketplaces, developers.openai.com/codex/plugins/build, and antigravity.google/docs/plugins + /docs/mcp. Record the exact required keys in a comment block at the top of `tests/test_manifests.py`, with source URLs. Where the docs are silent, follow the spec §3 layout and mark it `# UNVERIFIED`.
- [ ] **Step 2: Write the failing tests.**
  - `test_manifests.py`:
    - Every JSON parses.
    - Name/version agree across the three plugin manifests.
    - The MCP command/args in `.mcp.json` and `mcp_config.json` equal `install.MCP_SERVER`.
    - The Codex manifest `skills` key == `"./skills/"`.
    - The marketplace sources point at the repo root.
  - `test_install.py` (fake `home` in a temp dir):
    - `test_codex_copies_skills_and_appends_toml` → `home/.agents/skills/chords/SKILL.md` exists, and `config.toml` contains `[mcp_servers.soundcraft]`.
    - `test_idempotent` — a second run → the TOML header appears once, and no second backup is created when nothing changed.
    - `test_backup_before_edit` — an existing config → a `config.toml.bak-*` file exists with the original content.
    - `test_antigravity_merges_json` — an existing `mcp_config.json` with another server → both servers are present.
    - `test_dry_run_writes_nothing` — the dry-run returns action lines and the home tree is unchanged.
- [ ] **Step 3: Run.** Expect FAIL.
- [ ] **Step 4: Implement the manifests and `install.py`.**
  - The TOML edit is text-based: append the block if the header is missing (no TOML writer in stdlib).
  - Backups are named `<file>.bak-YYYYmmddHHMMSS`.
  - `--link` makes symlinks, falling back to a copy with a warning if symlinks fail (Windows without dev mode).
- [ ] **Step 5: Run** `claude plugin validate .` (expect no errors) and the full suite (expect PASS).
- [ ] **Step 6: Check the `model:` frontmatter.** If `codex` or `agy` is on PATH, try loading a temp skill with `model: sonnet` and record whether it errors. Write the result to `docs/harness-notes.md`. Do not add `model:` to the skills unless both harnesses are verified to tolerate it.
- [ ] **Step 7: Commit** `feat: harness manifests and fallback installer`

---

### Task 10: Skill linter and reference-spec checker

**Model:** sonnet

**Files:**
- Create: `tools/lint_skills.py`
- Test: `tests/test_skills_lint.py`

**Interfaces:**
- Produces:
  - `lint_skill(skill_dir: Path) -> list[str]` (error strings) checking:
    - frontmatter fields allowed: name, description, license, metadata;
    - name rules;
    - description length;
    - the 7 H2 sections in order;
    - every `../soundcraft-core/scripts/<file>` and `scripts/<file>` reference resolves to an existing file;
    - every ```` ```json ```` block under `references/` or in SKILL.md that has a top-level `"tracks"` key passes `validate_spec`.
  - `lint_all(repo: Path) -> dict[str, list[str]]`
- Tests:
  - `test_lint_flags_bad_fixture` — a temp skill with a wrong name, missing sections, a dead script path and an invalid json spec → 4 distinct errors.
  - `test_repo_skills_clean` — `lint_all(repo)` has no errors for every existing `skills/*`. Only directories containing a SKILL.md are linted; the test skips if there are none yet.

- [ ] **Step 1: Write the failing tests.**
- [ ] **Step 2: Run.** Expect FAIL.
- [ ] **Step 3: Implement.** Frontmatter is parsed by hand (a `key: value` subset, no YAML lib).
- [ ] **Step 4: Run.** Expect PASS.
- [ ] **Step 5: Commit** `test: skill linter and reference spec checker`

---

### Tasks 11–17: Skills (prose + knowledge)

**Shared requirements for every skill task:**
- Follow the Global Constraints SKILL.md rules and the spec §4.5 framework (A–H).
- `Workflow` must include preflight → read state → act → re-read (C), the ≤3-iteration loop with FAIL/WARN (D), the `.mid` fallback when MCP is unavailable, and the plain-language report (H).
- Script calls use paths relative to the skill folder. Example: `python ../soundcraft-core/scripts/make_midi.py spec.json`. Add the line "run commands from this skill's directory".
- MCP command ids and params come **only** from `soundcraft-commands.md` (Task 1). If a command there is UNVERIFIED, the skill must say "find it with `list_commands` first".
- Every example spec is a ```` ```json ```` block that passes the linter (Task 10).
- Content is in our own words. Note any adapted idea's source repo in a final HTML comment `<!-- ideas: Korben00/ableton-producer-skills (MIT) … -->` so that Task 18 can collect the credits.
- Each task's verification is `python tools/lint_skills.py skills/<name>` → no errors, plus the full test suite passing. Then commit `feat(skill): <name>`.

#### Task 11: `soundcraft-core` + `soundcraft-setup` skills
**Model:** sonnet

**Files:** `skills/soundcraft-core/SKILL.md`, `skills/soundcraft-setup/SKILL.md`

- **core:**
  - Explains the three CLIs (args, outputs, exit codes) and the JSON spec field reference. Condense spec §4 into a table.
  - Links `references/soundcraft-commands.md`.
  - Direct use case: "export these chords to .mid".
- **setup:** the spec §5 setup flow, steps 1–4, verbatim in order.
  - Per-OS install guidance links to the GitHub Releases page.
  - Install Python with `winget install Python.Python.3` / `brew install python` / the distro package manager, only after the user confirms.
  - MCP config instructions for each harness, plus `install.py`.
  - Smoke test spec: C–G–Am–F, 4 bars → import → `bounce_mix` → pass if peak > -inf.

#### Task 12: `chords` skill + `references/genres.md`
**Model:** sonnet (or GPT via T3)

**Files:** `skills/chords/SKILL.md`, `skills/chords/references/genres.md`

- **Accepted input:** typed symbols, roman numerals, and natural-language briefs (§4.5-B).
- **Reharmonize mode:** announce one strategy before changing anything (§4.5-F).
- **Instrument choice:** read the corpus `~/.soundcraft-skills/plugins.json` first if it exists, else use `subtractive_synth`.
- **`genres.md`:** one H2 per genre, covering all 14 genres in spec §5. Each genre has:
  - BPM range, feel, 3 progressions (symbols + roman), voicing/rhythm advice, recommended instruments (built-in + free plugin);
  - one complete example spec.

#### Task 13: `drums` skill + `references/grooves.md`
**Model:** sonnet (or GPT via T3)

**Files:** `skills/drums/SKILL.md`, `skills/drums/references/grooves.md`

- **Skill rules:**
  - `drum_map` selection: `soundcraft` for `drum_synth`, `gm` for GM plugins, a custom map for named third-party kits only if the user supplies or confirms it.
  - Fills every 4 or 8 bars.
  - Subtle humanize by default.
  - Snare drag for lo-fi/hip-hop versus tight timing for house/techno (§4.5-F).
- **`grooves.md`:** the same 14 genres. Each has BPM, swing, a main groove, a variation, a fill, and one example spec.

#### Task 14: `plugins` skill + `references/free-plugins.md`
**Model:** sonnet

**Files:** `skills/plugins/SKILL.md`, `skills/plugins/references/free-plugins.md`

- **Workflow:** scan with `--write-corpus` → report by category + unsupported warnings → recommend → open the official download page → after the user installs, rescan and load via MCP using the exact name. Read parameter ranges before setting them. Apply the standard FX order (§4.5-G).
- **Hard rule:** never download or run an installer.
- **`free-plugins.md`:** ≥20 free plugins with CLAP/VST3/AU availability (synths, drums, EQ, comp, reverb, delay, saturation, utility).
  - Each entry has: name, developer, formats, OS, official URL, 1-line use.
  - Verify every URL with WebFetch, and every format against the vendor page. Drop anything that cannot be verified.

#### Task 15: `sound-design` skill + `references/synth-recipes.md`
**Model:** sonnet

**Files:** `skills/sound-design/SKILL.md`, `skills/sound-design/references/synth-recipes.md`

- **Recipes:** 8 recipes (pad, pluck, lead, bass, 808/sub, keys, brass-ish, arp). Each has waveform, filter type/cutoff Hz/resonance, amp ADSR ms, filter ADSR ms + amount, LFO, unison/detune.
- **Mapping:** map the recipes onto the `subtractive_synth` parameter names and ranges from Task 1, or mark them UNVERIFIED with a "read ranges via MCP first" instruction.
- **Presets:** save through the preset command from Task 1.
- **External synths:** if the user has an external synth in the corpus, give patch guidance in generic synth terms instead.

#### Task 16: `theory-coach` skill
**Model:** haiku

**Files:** `skills/theory-coach/SKILL.md`

- **Workflow:** take the user's `.mid` or `file.export_midi` from a named track → `analyze_midi.py --json` → explain key + confidence + runner-up, chords, roman numerals, and why it sounds that way (function, borrowed chords, voice leading).
- **Ambiguity:** `?` spans are reported as ambiguous, never guessed.
- **Hand-off:** reharm requests go to `chords`.
- **Tables:** `Style table` and `Spec pattern` may be N/A with a reason.

#### Task 17: `thai-flavor` skill + `references/thai-styles.md`
**Model:** sonnet (or GPT via T3). The main model reviews it for cultural and musical accuracy.

**Files:** `skills/thai-flavor/SKILL.md`, `skills/thai-flavor/references/thai-styles.md`

- **Styles:** ลูกทุ่ง, หมอลำ (ลายใหญ่, ลายน้อย, ลายสุดสะแนน), ป๊อปไทย, สามช่า. Each has:
  - scale/mode (Thai pentatonic sets as pitch-class lists);
  - typical progressions;
  - BPM;
  - a groove mapped onto **existing `VOICES` only** (e.g. ฉิ่ง→`ride` or `cowbell`, ฉาบ→`crash`/`open_hat`, กลองยาว/โทน/รำมะนา→toms/`perc`). State each mapping and why;
  - one chords spec + one drums spec.
- **Fusion:** guidance on mixing with pop/EDM.
- **Uncertain facts:** where a cultural or musical fact is uncertain, say so in the text rather than inventing it.
- **Hand-off:** the skill writes specs and hands off to `chords`/`drums`.

---

### Task 18: README, CREDITS and final verification

**Model:** haiku

**Files:**
- Create: `README.md` (Thai first, then English), `CREDITS.md`

- [ ] **Step 1: Write `README.md`.**
  - What it is, the skill list, requirements (SoundCraft, Python ≥3.9).
  - Install per harness:
    - Claude Code — `/plugin marketplace add <your-github>/soundcraft-skill`, then `/plugin install soundcraft-skills@<marketplace>`.
    - Codex — the plugin marketplace or `python install.py --codex`.
    - Antigravity — `agy plugin install <url>` or `python install.py --antigravity`.
  - Example prompts in Thai.
  - Roadmap (spec §10).
  - License line.
- [ ] **Step 2: Write `CREDITS.md`.** The spec §8 table, plus every repo named in `<!-- ideas: … -->` comments (`grep -r "ideas:" skills`). MIT sources keep their copyright line.
- [ ] **Step 3: Verify.** Run `python -m unittest discover -s tests -t .` → all PASS. Run `python tools/lint_skills.py` → no errors. Run `claude plugin validate .` → OK. Run `python skills/soundcraft-core/scripts/make_midi.py skills/soundcraft-core/examples/lofi-sketch.json --out out/lofi.mid` → exit 0.
- [ ] **Step 4: Commit** `docs: README and credits`

---

### Task 19: Live SoundCraft smoke test (needs user confirmation)

**Model:** sonnet

- [ ] **Step 1:** Ask the user before installing SoundCraft (Windows MSI/zip from GitHub Releases). If they decline, record `SKIPPED` in `docs/harness-notes.md` and stop.
- [ ] **Step 2:** Run the setup skill's smoke test through `soundcraft-cli run … --bounce out/smoke.wav`, or through MCP. Record peak/LUFS.
- [ ] **Step 3:** Run one chords and one drums example through import + bounce. Correct any wrong command ids or params found in `soundcraft-commands.md` and the skills, and re-run the lint and tests.
- [ ] **Step 4: Commit** `test: live soundcraft smoke test results`
