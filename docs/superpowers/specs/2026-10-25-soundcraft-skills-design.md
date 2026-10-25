# SoundCraft Skills — Design Spec

- Date: 2026-10-25
- Status: approved (Phase 1 detailed, Phases 2–3 at roadmap level)
- Target program: [storytold/soundcraft](https://github.com/storytold/soundcraft) (Rust DAW, pre-alpha)

## 1. Goals

A set of Agent Skills that help music producers save time making music with SoundCraft:
generate chord progressions, generate drum patterns, and find/install/use the plugins (CLAP/VST3/AU) the producer owns.

**Users:** for personal use first, published later — so the design must work across OSes (Windows/macOS/Linux)
and across agent harnesses from the start.

**Supported harnesses:** Claude Code, OpenAI Codex (GPT), Google Antigravity

All repository files are written in English; skills reply to the user in the user's language.

**v1 success criteria**
1. The user types chord names directly (`Am7 - Fmaj7 - C - G/B`) or describes them in plain language
   ("sad lo-fi chords in D minor") and gets a playable chord track in SoundCraft
2. The user asks for drums by genre/BPM and gets a drum track in SoundCraft
3. The user asks which plugins they have / which to use, gets an answer from a real scan of their machine, and can load a plugin onto a track
4. If SoundCraft/MCP is unavailable, the user still gets a `.mid` file to use in another DAW
5. Installable on all 3 harnesses from a single repo
6. The user asks for a sound ("warm pad", "long 808") and gets a configured `subtractive_synth` + a saved preset
7. The user provides an existing MIDI file / track and gets the key, chord names, Roman numerals, and an explanation
8. Asking for "Luk thung (ลูกทุ่ง)" / "Mor lam (หมอลำ)" / "Thai pop (ป๊อปไทย)" in chords/drums gives the correct Thai idiom

**The work is split into 3 phases** (see §10 Roadmap) — this spec details **Phase 1**;
Phases 2–3 will get their own spec + plan once the previous phase is usable in practice.

**Out of scope for all phases:** automatically downloading/running plugin installers

## 2. SoundCraft facts the design relies on

- Built-in MCP server: `soundcraft-cli mcp` — tools `list_commands`, `execute`, `batch`,
  `inspect_session`, `new_session`, `open_session`, `save_session`, `import_audio`, `bounce_mix`, `parity`
- Commands are an id + JSON params, e.g. `mix.insert={"track":"Bass","plugin":"eq_7band"}`,
  `mix.instrument`, `track.new`, `file.import_midi`, `file.export_midi`
- 25 built-in plugins (e.g. `subtractive_synth`, `drum_synth`, `eq_7band`, `compressor`)
- External plugins: CLAP, VST3, AU (macOS) — VST2/AAX/LV2/LADSPA not supported; scanned from standard system folders; no registry/installer
- There is no documented command for creating notes — v1 generates a `.mid` and then runs `file.import_midi`

**To be confirmed from source during implementation** (record results in `soundcraft-commands.md`):
the params of `file.import_midi`, `mix.instrument`, the command for loading external plugins, the note map of `drum_synth`,
and whether the `--demo` flag is required

## 3. Architecture

```
soundcraft-skill/
├── skills/
│   ├── soundcraft-core/
│   │   ├── SKILL.md
│   │   ├── scripts/
│   │   │   ├── make_midi.py          # CLI: JSON spec -> .mid + text summary
│   │   │   ├── scan_plugins.py       # CLI: scan plugin folders -> JSON + corpus
│   │   │   ├── analyze_midi.py       # CLI: .mid -> key, chords, Roman numerals (JSON/text)
│   │   │   └── scmidi/
│   │   │       ├── midi_reader.py    # read SMF (used by both analyze and tests)
│   │   │       ├── analysis.py       # key guessing (pitch-class profile), chord detection per time window
│   │   │       ├── theory.py         # parse chords/Roman numerals, voicing, voice leading
│   │   │       ├── rhythm.py         # step string parser, swing, humanize, fill
│   │   │       ├── drums.py          # drum maps (gm, soundcraft, custom)
│   │   │       ├── spec.py           # validate JSON spec -> readable errors
│   │   │       └── midi_writer.py    # write SMF type 1 (pure stdlib)
│   │   └── references/soundcraft-commands.md
│   ├── soundcraft-setup/SKILL.md
│   ├── chords/{SKILL.md, references/genres.md}
│   ├── drums/{SKILL.md, references/grooves.md}
│   ├── plugins/{SKILL.md, references/free-plugins.md}
│   ├── sound-design/{SKILL.md, references/synth-recipes.md}
│   ├── theory-coach/SKILL.md
│   └── thai-flavor/{SKILL.md, references/thai-styles.md}
├── .claude-plugin/{plugin.json, marketplace.json}   # Claude Code
├── .mcp.json                                        # Claude Code + Codex
├── .codex-plugin/plugin.json                        # Codex
├── .agents/plugins/marketplace.json                 # Codex marketplace
├── plugin.json, mcp_config.json                     # Antigravity
├── LICENSE, CREDITS.md                               # MIT (Chaiyaporn Santangjai) + credits
├── install.py                                       # fallback installer
├── tests/
└── README.md                                        # (English)
```

**Principles**
- A single `skills/` set shared by all harnesses
- All scripts live in `soundcraft-core` (because some harnesses copy only the skill folder)
  other skills reference `../soundcraft-core/scripts/...` relative to their own skill folder
- Python 3.9+ pure stdlib, no dependencies
- Frontmatter uses only the fields from the Agent Skills spec (`name`, `description`, `license`, `metadata`)
  — `model:` (Claude-only, for cost savings) will be added only after testing confirms Codex/Antigravity do not error
- `install.py`: copies/symlinks `skills/*` to `~/.agents/skills` (Codex) and `~/.gemini/config/skills` (Antigravity),
  merges MCP config into `~/.codex/config.toml` and `~/.gemini/config/mcp_config.json` using absolute paths;
  has `--dry-run` and backs up config files before editing
- Every manifest is checked against the official docs during implementation (the marketplace format for Claude/Antigravity
  and the Codex `mcpServers` key are not yet confirmed)

**Data flow (chords/drums)**
User request → skill interprets (using references) → writes JSON spec to a file → `make_midi.py spec.json`
→ `.mid` + note summary → MCP `file.import_midi` → `mix.instrument` → (optional) `bounce_mix` to check there is sound

## 4. JSON Spec

```json
{
  "bpm": 90, "time_signature": [4, 4], "key": "D minor",
  "output": "lofi-sketch.mid",
  "tracks": [
    {
      "name": "Chords", "type": "chords",
      "progression": ["Dm9", "Gm7", {"chord": "Bbmaj7", "beats": 2}, "A7b9"],
      "chord_length": "1bar",
      "voicing": "open", "octave": 4,
      "rhythm": "pad", "velocity": 80, "humanize": 0.15, "repeat": 2
    },
    {
      "name": "Drums", "type": "drums",
      "steps": 16, "swing": 0.58, "bars": 8,
      "pattern": {
        "kick":  "x.....x...x.....",
        "snare": "....X.......X..g",
        "hat":   "x.x.x.x.x.x.x.x."
      },
      "fill": {"every": 4, "pattern": {"snare": "........x.x.XxXx"}},
      "drum_map": "gm"
    }
  ]
}
```

**Chords track**
- `progression`: a string or `{"chord", "beats"|"bars"}`; also accepts a single string separated by `-` or `|`
- Chord qualities: triad, `m`, `dim`, `aug`, `sus2`, `sus4`, `5`, `6`, `m6`, `7`, `maj7`, `m7`, `mMaj7`,
  `m7b5`, `dim7`, `9`, `maj9`, `m9`, `11`, `m11`, `13`, `maj13`, `add9`, `add11`,
  alterations (`b5 #5 b9 #9 #11 b13`), slash chord (`G/B`)
- Roman numerals when `key` is present: `i - VI - III - VII`, `ii7 - V7 - Imaj7`, supports `bVII`, `V/V`
- `voicing`: `close` | `open` | `drop2` | `spread` | `rootless` (3-5-7-9, MIDI range ~56–74, used when a bass plays the root);
  `range: [low, high]` forces the note range per instrument (default `[48, 79]`); automatic voice leading (picks the inversion with the smallest total distance), can be turned off with `"voice_leading": false`
- `rhythm`: `block` | `pad` | `stabs` | `arp-up` | `arp-down` | `arp-updown` | `custom` (+ `"steps"` string)
- `bass_note`: `true` adds a root one octave lower (default `false`)
- `strum_ms`: delays each note in the chord from bottom to top (default 0; ~15 recommended for piano/guitar)

**Drums track**
- step chars: `x` normal (vel 100), `X` accent (vel 120), `g` ghost (vel 45), `.` rest
- String length = `steps` per bar (default 16); may span more than 1 bar if it is a multiple of `steps`
- Sounds: `kick snare clap rim hat open_hat pedal_hat ride crash tom_hi tom_mid tom_low shaker tambourine cowbell perc`
- `swing` 0.5–0.75 (shifts odd steps), `humanize` 0–1 (randomizes timing ±/velocity with a fixed seed — `"seed"` is configurable)
- `offset_ms`: shifts individual sounds across the whole pattern, e.g. `{"snare": 25}` (snare laid back for lo-fi/hip-hop)
- `velocity`: overrides the `x/X/g` values per sound, e.g. `{"hat": {"x": 85, "g": 40}}`
- `fill.every` N bars replaces the last bar of every N bars, only for the specified sounds
- `drum_map`: `gm` | `soundcraft` | object `{"kick": 36, ...}`

**Output**
- SMF type 1, PPQ 480, tempo + time signature in track 0, one track per spec track
- Drums use channel 10, chords use channel 1+ in order
- stdout: a per-bar text summary (`Bar 1: Dm9 = D3 A3 C4 E4 F4`) + file path
- `--json` gives the summary as JSON
- Exit code: 0 success, 2 invalid spec (message names the field + value + what is accepted)
- Always validate before writing: pitch 0–127, velocity 1–127, start ≥ 0, duration > 0 — never write output that has not passed validation

## 4.5 Thinking Framework (the approach shared by every skill)

Adapted from the reference repos (see §8) to fit SoundCraft — rewritten entirely in our own words

**A. Standard SKILL.md structure** — every skill has the same headings:
`When to use` → `Workflow` → `Style table` → `Spec pattern` → `Checks` → `Limits` → `Related skills`

**B. Brief → Parameters** (used in chords/drums) — break the request into
key/scale, bpm, bars, genre/feel, mood, density (sparse↔busy), energy arc, target instrument/plugin
- Fill missing values from the Style table of that genre, then **tell the user what was chosen for them**
- Ask only when truly necessary (e.g. genre unknown and no context at all), at most 1–2 questions, in confirm style:
  "I'll use D minor, 90 BPM, lo-fi style. OK?" rather than open-ended questions

**C. Preflight → Read state → Act → Re-read** (every time SoundCraft is touched)
1. Preflight: does MCP respond (`list_commands`) — if it fails, stop and send to `soundcraft-setup` / fall back to `.mid`
2. Read state: `inspect_session` to get real track names/ids — **never guess an id**
3. Plugin: look up the exact name before loading (a wrong-case name fails)
4. Never overwrite existing tracks/clips unless the user says so — the default is to create a new track
5. After every change: `inspect_session` to confirm the result

**D. Generate → Measure → Adjust (at most 3 rounds)**
- Spec-level measure: read the note summary from `make_midi.py` and check it against intent (chords correct, range within bounds, kick on the right beats)
- Audio-level measure (if MCP is available): `bounce_mix` → has sound (peak > -inf), no clipping (peak ≤ 0 dBFS)
- If still failing after 3 rounds → report what is stuck and ask the user
- Results are split into **FAIL** (stop) / **WARN** (report but continue)

**E. Error recovery classes** (in `soundcraft-commands.md`)
| Class | Example | Fix |
|---|---|---|
| Fix the request | invalid spec, wrong command/plugin name | fix and rerun / `list_commands` to find a similar command |
| Fix session state | track missing, transport is playing | re-read state / stop transport before changing structure |
| Fix the environment | SoundCraft not open, MCP not connected, file not writable | send to setup / fall back to `.mid` |

**F. Music knowledge embedded in references**
- *Harmony* (`chords`): extend chords by genre (m→m9, maj→maj9, dom→9/13 for R&B/jazz/neo-soul),
  rootless voicing when there is a bass, modal interchange (♭III ♭VI ♭VII iv), tritone sub, passing diminished;
  **reharmonize** mode — "make it jazzier/sadder" must **announce 1 strategy first**, then make the change
- *Rhythm* (`drums`): 3 velocity levels (accent/normal/ghost), swing only on off-beat 16ths,
  laid-back snare (lo-fi/hip-hop) vs exactly on the beat (house/techno), fill every 4 or 8 bars,
  light humanize as the default ("too much humanize makes genres that need to be tight sloppy")
- *Style table* per genre: BPM range, feel, example progression/groove, recommended instruments (built-in + free plugins)

**G. User Corpus** (`plugins`)
- Plugin scan results are stored at `~/.soundcraft-skills/plugins.json` (name, format, path, category: synth/drum/eq/comp/reverb/…)
- `chords`/`drums` read the corpus to recommend **plugins the user actually has** before built-ins or free ones not yet installed
- Always read parameter ranges from MCP before setting values; standard FX order: EQ → comp → saturation → modulation → delay → reverb

**H. Reporting results** — short plain language: what was done, which values were chosen and why, where the file is, the recommended next step

## 5. Skills

| Skill | Role |
|---|---|
| `soundcraft-core` | Documentation for how to call the scripts + MCP commands; directly usable for "export as .mid" |
| `soundcraft-setup` | Check/guide installation of SoundCraft + Python, set up MCP per harness, smoke test |
| `chords` | Interpret request → spec → import → set instrument (default `subtractive_synth` or a plugin the user specifies) |
| `drums` | Interpret genre/BPM/feel → spec → import → `drum_synth` or the user's drum plugin (choose `drum_map`) |
| `plugins` | Scan → report → recommend free plugins (open the download page, do not run the installer) → load onto a track |
| `sound-design` | Sound description → `subtractive_synth` recipe (osc, filter, envelope, LFO) → read param ranges from MCP → set values → save preset; if the user has an external synth (corpus), give patch advice instead |
| `theory-coach` | The user's `.mid` or `file.export_midi` from a track → `analyze_midi.py` → explain key/chords/Roman numerals/voice leading and "why it sounds this way"; propose a reharm by handing off to `chords` |
| `thai-flavor` | Thai idiom: Luk thung, Mor lam (Lai yai (ลายใหญ่), Lai noi (ลายน้อย), Lai sut sanaen (ลายสุดสะแนน)), Thai pop, Sam cha (สามช่า); Thai pentatonic, patterns for klong yao (กลองยาว), thon (โทน), rammana (รำมะนา), ching (ฉิ่ง), chap (ฉาบ) mapped onto GM drum sounds; how to blend with pop/EDM; hands the spec to `chords`/`drums` to generate |

**sound-design recipes** (`synth-recipes.md`): pad, pluck, lead, bass, 808/sub, keys, brass-ish, arp —
each specifies waveform, filter type/cutoff/resonance, ADSR amp+filter, LFO, unison/detune as values described in
real units (Hz, ms), then mapped onto the `subtractive_synth` params during implementation (param names/ranges confirmed from source)

**theory-coach analysis**: key via the Krumhansl–Schmuckler profile (reports confidence + the 2nd-ranked alternative),
chords per window (default 1 beat, merging repeated windows) via reverse template matching with `theory.py`;
unclear windows are labeled `?` instead of guessing

**Knowledge library** (`genres.md`, `grooves.md`): pop, Thai pop/Luk thung, ballad, R&B/neo-soul, hip-hop, trap, lo-fi,
house, techno, rock/indie, funk, jazz, latin/reggaeton, afrobeats — each genre has a progression/voicing/rhythm or
groove + typical BPM, as example specs that can be adapted. For genres not in the library the agent uses its own music theory

**soundcraft-setup flow**
1. `soundcraft-cli --version` → missing: explain how to install per OS + Releases link, proceed once the user confirms
2. Python 3 → missing: recommend `winget install Python.Python.3` / `brew install python` / the package manager, run when the user permits
3. MCP `list_commands` → fails: show the setup steps for the harness in use, or recommend `install.py`
4. Smoke test: C–G–Am–F, 4 bars → import → `bounce_mix` → report peak/LUFS (peak > -inf = pass)

**plugins: scanned folders**
- Windows: `%CommonProgramFiles%\VST3`, `%CommonProgramFiles%\CLAP`, `%LOCALAPPDATA%\Programs\Common\VST3`, `%LOCALAPPDATA%\Programs\Common\CLAP`
- macOS: `/Library/Audio/Plug-Ins/{VST3,CLAP,Components}`, `~/Library/Audio/Plug-Ins/{VST3,CLAP,Components}`
- Linux: `~/.vst3`, `~/.clap`, `/usr/lib/vst3`, `/usr/local/lib/vst3`, `/usr/lib/clap`, `/usr/local/lib/clap`, `$CLAP_PATH`
- Report unsupported formats (VST2 `.dll`/`.vst`, AAX, LV2) separately as warnings
- `--extra-dir` adds extra folders

## 6. Error handling

- No MCP / SoundCraft not working → every skill still generates a `.mid` and tells the user the path so they can drag it into a DAW themselves
- Invalid spec → exit 2 + clear message → the agent fixes it and reruns (at most 3 rounds, then asks the user)
- Wrong/version-changed MCP command → the skill uses `list_commands` to find a similar command before telling the user
- Plugin does not show up → recommend restart/rescan + known limitations (signed macOS does not load external VST3, in-process crash)
- Actions that modify the system (installing programs, editing harness config) → always require user confirmation first

## 7. Testing

- `python -m unittest` (stdlib):
  - theory: parse every chord quality, slash, Roman numerals, voicing, voice leading
  - rhythm/drums: step parser, swing, humanize with a fixed seed, fill, drum maps
  - spec: error messages for invalid input
  - midi_writer: read the written `.mid` back with the reader in the tests, check notes/ticks/tempo
  - scan_plugins: mock folders in a temp dir
  - install.py: `--dry-run` with a mock home
- Lint skills: a script that checks every SKILL.md (name matches folder name, `a-z0-9-`, ≤64 chars, description ≤1024)
- `claude plugin validate .`
- Integration (if SoundCraft is available): `soundcraft-cli run --cmd ... --bounce` from the smoke test
- Codex/Antigravity: check the file structure against the docs; the user tests actual installation

## 8. References and License

- This project: MIT — Copyright (c) 2026 Chaiyaporn Santangjai (`LICENSE`)
- `CREDITS.md` lists every repo that contributed ideas, with its license
- Policy: write new content in our own words, do not copy long passages; if adapting text from an MIT repo, keep the copyright notice in `CREDITS.md`

| Repo | License | What was taken |
|---|---|---|
| Goldwaterfung/Stratawright | MIT | preflight/read-state, exact-name lookup, error recovery classes, analyze→fix→re-analyze |
| Korben00/ableton-producer-skills | MIT | SKILL.md structure, brief→parameters, validate-before-write, harmony/rhythm/humanize rules |
| bitwize-music-studio/claude-ai-music-skills | CC0-1.0 | gated FAIL/WARN, confirm-style questions, example cross-harness manifests, LUFS targets (v2) |
| rtmalikian/tech-house-production-skills | no LICENSE file | ideas only: generate→measure→adjust ≤3 rounds, tech house numbers (v2) |
| glincker/ableton-skills | MIT | voicing by instrument range, groove-builder |
| kennethreitz/pytheory | MIT | music theory logic reference (to check parser output) |
| dreamrec/LivePilot | BSL-1.1 | ideas only: User Corpus |

**Knowledge backlog for v2:** gain staging/LUFS targets/EQ-comp tables (tech-house, bitwize) → mix-assist;
arrangement templates + "something must change every 8 bars" → song-sketch; bassline/topline rules (Korben) → bassline/melody

## 9. Cost plan (implementation)

Sub-tasks that need no design decisions (genres/grooves library, free-plugins, tests, README, manifests)
are delegated to cheap subagents (Sonnet 5.5 / Haiku 5.5 / GPT via T3) — core work (theory, midi_writer, spec)
and reviews are done by the main model

## 10. Roadmap

| Phase | Skills | Needs from previous phase |
|---|---|---|
| **1** (this spec) | soundcraft-core, soundcraft-setup, chords, drums, plugins, sound-design, theory-coach, thai-flavor | — |
| **2** | bassline-melody, groove-humanize, session-template, reference-brief | theory.py, midi_reader, corpus, a working MCP flow |
| **3** | song-sketch, mix-assist, export-delivery, producer-next-step | every skill from phases 1–2 + the mix/LUFS knowledge in the §8 backlog |

- **bassline-melody**: bass following chords (R/5/8 rhythm templates, "kick controls the downbeat, bass controls the off-beat"), topline (chord tones on strong beats, 2/4-bar phrases, call-response)
- **groove-humanize**: apply swing/humanize/feel to existing MIDI (`midi_reader` → transform → rewrite)
- **session-template**: create a genre-based session in one command (tempo, tracks, instruments, buses, basic FX)
- **reference-brief**: reference song/artist name → style profile (BPM, key, groove, palette) handed to other skills — does not download or analyze copyrighted audio files
- **song-sketch**: a whole song structure (intro/verse/chorus/drop) including chords+drums+bass, with the rule "something must change every 8 bars"
- **mix-assist**: bounce → LUFS/peak → recommend/adjust eq_7band/compressor step by step, re-measure
- **export-delivery**: bounce master + stems, LUFS targets per platform (streaming -14 / club ~-8), export MIDI
- **producer-next-step**: read the session and recommend the next step ("no bass yet", "chorus is not different from verse yet")
