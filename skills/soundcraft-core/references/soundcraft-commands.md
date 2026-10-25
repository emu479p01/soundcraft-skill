# SoundCraft command reference (verified)

Verified on 2026-10-25 against https://github.com/storytold/soundcraft (HEAD, via WebFetch of raw files only; nothing cloned or executed). SoundCraft is pre-alpha, so re-verify with the `list_commands` MCP tool when in doubt. Anything not found in source is marked `UNVERIFIED (looked in: ...)`.

Source key: `docs/mcp.md`, `docs/control-protocol.md`, `docs/plugin-parity.md`, `AGENTS.md`, `crates/engine/src/cmd/*.rs`, `crates/automation/src/mcp.rs`, `apps/soundcraft-cli/src/main.rs`, `crates/dsp/src/plugins/*.rs`, `crates/{vst3,clap}-host/src/scan.rs`.

## MCP server

- Binary: `soundcraft-cli`. Transport: stdio. Source: `apps/soundcraft-cli/src/main.rs`, `docs/mcp.md`.
- Usage line (verbatim): `soundcraft-cli mcp [--connect PORT] [--demo] [--automation-read-root DIR]... [--automation-write-root DIR]...`
- Headless (default): no window, no audio device. `--demo` only starts from the demo session; it is NOT required. Without it the engine starts empty (use `new_session`). Source: `docs/mcp.md`.
- Desktop bridge: start app with `soundcraft --control 7801`, then `soundcraft-cli mcp --connect 7801` (adds screenshot/click tools).
- Claude Code registration (docs): `claude mcp add soundcraft -- soundcraft-cli mcp --demo`.
- `--automation-read-root DIR`: confines commands that load files (`open_session`, `import_audio`, `file.import_midi`, `track.load_preset`). Repeatable.
- `--automation-write-root DIR`: confines commands that write files (`save_session`, `bounce_mix`, `file.export_midi`, `track.save_preset`; session saves also write `Audio Files/`, `Backups/`, and a temp file). Repeatable.
- Read and write are separate: a folder needs both flags to get both. A kind left out grants none of that access. Roots must exist; paths are resolved absolute and links followed; a path outside a root returns an ordinary tool error. Combining roots with `--connect` is an error.
- Roots do NOT cover: pathless commands, plugin discovery (loads binaries from system folders), recording (desktop only).
- Resources: `soundcraft://session`, `soundcraft://commands`.
- Conventions: programmatic calls never open dialogs; empty params act on the current selection; positions are sample counts, `{"seconds": x}`, or bars-beats strings; tracks by name or id, clips by id; edits undoable via `edit.undo`.

## MCP tools

Source: `crates/automation/src/mcp.rs` (`tool_definitions()`), `docs/mcp.md`.

| Tool | Params JSON | Example |
|---|---|---|
| `list_commands` | `{filter?: string}` (matches id or label, substring) | `{"filter":"mix."}` |
| `execute` | `{command: string, params?: object}` | `{"command":"mix.volume","params":{"track":"Kick","db":-6}}` |
| `batch` | `{calls: [{command, params}] (max 1000), keep_going?: bool}` | stops at first error unless `keep_going` |
| `inspect_session` | `{detail?: "summary" or "full"}` | `{"detail":"full"}` |
| `new_session` | `{name?, sample_rate?: int, template?: "blank" or "demo"}` | `{"name":"Song","sample_rate":48000}` |
| `open_session` | `{path}` (returns `missing` media) | `{"path":"/x/song.scraft"}` |
| `save_session` | `{path?, replace?: bool}` (`replace` needed to overwrite) | `{"path":"/x/song.scraft","replace":true}` |
| `import_audio` | `{path, track?: string or int, at?}` (WAV, AIFF, FLAC, MP3, OGG, AAC/M4A, ALAC, CAF) | `{"path":"/x/a.wav"}` |
| `bounce_mix` | `{path, format?: wav, aiff or flac, bit_depth?: string, start?, end?, normalize?: bool}`; returns peak dBFS and integrated LUFS | `{"path":"/x/out.wav","format":"wav"}` |

Also: `parity`; desktop-only (`--connect`): `screenshot`, `ui_inspect`, `ui_set`, `menu_invoke`, `click`, `drag`, `key`.

Tool errors: normal result with `isError: true`, text is the message (e.g. `` `command` required ``, `` unknown tool `{name}` ``). A failed batch returns `isError: true` with a JSON array of `{command, ok, result|error}`. Over 1000 calls: "`calls` must contain at most 1000 commands; no commands were executed". Protocol errors are JSON-RPC (`-32700`, `-32600`, `-32601`, `-32002`).

## Commands we use

Every row: id, params, example, source.

| Id | Params | Example | Source |
|---|---|---|---|
| `track.new` | `{count?: 1, format?: mono/stereo/5.1, kind?: audio/aux/master/midi/instrument/vca/folder, name?, timebase?: samples/ticks, instrument?: plugin id}` | `{"kind":"instrument","name":"Drums","instrument":"drum_synth"}` | `cmd/track.rs` |
| `file.import_midi` | `{path, at?: 0, tempo_map?: true}` (tempo_map read by code, not in doc string); returns `{tracks}` | `{"path":"/x/drums.mid"}` | `cmd/file.rs` |
| `file.export_midi` | `{path, tracks?}` (alias `track`); only MIDI tracks; returns `{path, bytes}` | `{"path":"/x/out.mid","tracks":["Drums"]}` | `cmd/file.rs` |
| `mix.instrument` | `{track?, plugin: id, params?: {id: value}}`; plugin may be built-in, `clap:`, `vst3:`, `au:`; other fields rejected; instrument tracks only; params clamped | `{"track":"Lead","plugin":"subtractive_synth","params":{"cutoff":800}}` | `cmd/instrument.rs` |
| `mix.instrument_param` | `{track?, param, value}` built-in instruments only | `{"track":"Lead","param":"cutoff","value":1200}` | `cmd/instrument.rs` |
| `mix.insert` | `{track?, slot?: 0..9 or a..j, plugin: id, params?: {id: value}}` | `{"track":"Drums","plugin":"compressor"}` | `cmd/mix.rs` |
| `mix.volume` | `{tracks?, db: -144..12, or delta_db}` | `{"tracks":["Kick"],"db":-6}` | `cmd/mix.rs` |
| Third-party plugin load | No dedicated command. Use `mix.insert` (effects) or `mix.instrument` (instruments) with `plugin` = `vst3:<class id hex>`, `clap:<id>`, or `au:<type>:<subtype>:<manufacturer>`. Get ids from the list commands below. | `{"track":"Lead","plugin":"vst3:ABCD..."}` | `cmd/clap.rs` (`plugin_info` lookup order), `cmd/vst3.rs`, `cmd/instrument.rs` |
| Plugin rescan / list | `engine.vst3_plugins {rescan?: bool}` and `engine.clap_plugins {rescan?: bool}`; entries carry `id`, name, vendor, version, `is_instrument`, `path` | `{"command":"engine.vst3_plugins","params":{"rescan":true}}` | `cmd/vst3.rs`, `cmd/clap.rs`. Whether these are reachable via MCP `execute` is UNVERIFIED (looked in: mcp.rs, mod.rs); confirm with `list_commands` filter `plugins`. |
| Preset save | `track.save_preset {path, track?}` writes JSON (format `soundcraft-track-preset` v1: type, width, mixer, inserts, sends, instrument). Errors: "`path` required", "no track". | `{"path":"/x/lead.json","track":"Lead"}` | `cmd/track_more.rs`. This is a TRACK preset; per-plugin presets UNVERIFIED (looked in: plugin_state.rs, track_more.rs). |
| Preset load | `track.load_preset {path, tracks?}`. Errors: "`path` required", "not a SoundCraft track preset". | `{"path":"/x/lead.json"}` | `cmd/track_more.rs` |
| Set plugin parameter | Insert effect: `mix.insert_param {track?, slot, param, value}` or batch `mix.insert_params {track?, slot, params: {id: value}, preset?: name}`. Instrument: `mix.instrument_param`. Values clamped; unknown ids and non-numeric values are errors. | `{"track":"Drums","slot":0,"param":"threshold","value":-18}` | `cmd/mix.rs`, `cmd/instrument.rs`. Raw state: `mix.insert_state {track, slot or "instrument", state: base64 or null}` (`cmd/plugin_state.rs`). |
| Read plugin parameter ranges | UNVERIFIED (looked in: mcp.rs, cmd/mod.rs, cmd/mix.rs, cmd/instrument.rs, cmd/plugin_state.rs, cli `describe`/`plugins`). `soundcraft-cli plugins` prints only id/name/category; `describe ID` is for command ids. `inspect_session` may list inserts but range exposure is unconfirmed. Ranges for the two instruments are in the tables below (from `crates/dsp`); for effects read `crates/dsp/src/plugins/<category>.rs`. Out-of-range values are clamped, not rejected. | n/a | n/a |
| `transport.stop` | `{}` (siblings: `transport.play {from?}`, `transport.status {}`, `transport.locate {at}`) | `{"command":"transport.stop","params":{}}` | `cmd/transport.rs` |

Other useful (same sources): `mix.pan {tracks?, pan: -1..1}`, `mix.mute`, `mix.solo`, `mix.send {track?, slot?, bus, level_db?}`, `mix.new_bus {name}`, `mix.insert_remove {track?, slot}`, `mix.insert_bypass`, `track.rename {track, name}`, `track.delete {tracks?}`, `edit.undo`, `file.bounce_mix {path, format?, bit_depth?, start?, end?, source?, normalize?, dither?, fold_down?}`, `session.save {path?, replace?}`.

## Built-in plugins

25 effect ids (source: `docs/plugin-parity.md`):

| Category | Ids |
|---|---|
| EQ | `eq_1band`, `eq_7band`, `channel_strip` |
| Dynamics | `compressor`, `expander_gate`, `de_esser`, `maximizer` |
| Reverb | `room_reverb`, `plate_reverb` |
| Delay | `mod_delay` |
| Modulation | `chorus`, `flanger`, `phaser`, `ring_mod` |
| Harmonic | `lofi`, `rectifier`, `saturator` |
| Pitch and time | `pitch_shifter`, `time_shift` |
| Utility | `trim`, `gain`, `invert`, `dc_offset_removal`, `signal_generator`, `dither` |

Instruments (category Instrument, `is_instrument: true`; source `crates/dsp/src/plugins/{synth,drums}.rs`, `cmd/instrument.rs`): `subtractive_synth` (default for new instrument tracks), `drum_synth`. `docs/plugin-parity.md` says "3 instruments"; the third (likely a sampler, see `crates/dsp/src/plugins/sampler.rs`, `cmd/sampler.rs`) is UNVERIFIED (looked in: plugin-parity.md, instrument.rs). Instruments are counted separately from the 25 effects.

Plugin errors: "unknown plugin `{plugin}`", "`{plugin}` is not an instrument", "`{plugin}` has no parameter `{k}`".

## subtractive_synth parameters

Source: `crates/dsp/src/plugins/synth.rs` (`SYNTH_PARAMS`, 19). Values clamped into range.

| id | range | default | unit |
|---|---|---|---|
| `osc1_wave` | choice 0 Saw, 1 Square, 2 Sine, 3 Triangle | 0 | - |
| `osc2_wave` | choice (same) | 0 | - |
| `osc2_semitones` | -24..24 | 0 | semitones |
| `osc2_detune` | -100..100 | 7 | cents |
| `osc_mix` | 0..100 | 50 | percent |
| `cutoff` | 20..20000 (log) | 2000 | Hz |
| `resonance` | 0..100 | 20 | percent |
| `filter_env_amount` | -100..100 | 30 | percent |
| `amp_attack` | 0.5..5000 (log) | 5 | ms |
| `amp_decay` | 1..5000 (log) | 200 | ms |
| `amp_sustain` | 0..100 | 70 | percent |
| `amp_release` | 1..10000 (log) | 300 | ms |
| `filter_attack` | 0.5..5000 (log) | 5 | ms |
| `filter_decay` | 1..5000 (log) | 300 | ms |
| `filter_sustain` | 0..100 | 30 | percent |
| `filter_release` | 1..10000 (log) | 300 | ms |
| `glide` | 0..1000 | 0 | ms |
| `velocity` | 0..100 | 70 | percent |
| `level` | -48..6 | -6 | dB |

## drum_synth

Source: `crates/dsp/src/plugins/drums.rs` (`kind_for`). The map is GM-inspired but CUSTOM (it differs from the standard GM percussion map; see the final `drum_synth map:` line), 24-voice pool, closed hat (42/44) chokes open hat (46).

| MIDI note | voice |
|---|---|
| 35, 36 | kick |
| 38, 40 | snare |
| 37, 39 | clap |
| 42, 44 | closed hat |
| 46 | open hat |
| 41, 43 | floor tom (82 Hz) |
| 45 | low tom (110 Hz) |
| 47, 48 | mid tom (147 Hz) |
| 50 | high tom (196 Hz) |
| 49, 57 | crash |
| 51, 59 | ride |

Notes not listed (e.g. 52-56, 58, 60+) are not mapped in the source excerpt read; their behaviour is UNVERIFIED (looked in: drums.rs match summary). Note 37 (GM side stick) plays a clap here, and 44 plays a closed hat; there is no rimshot, shaker, tambourine, cowbell or perc voice. Notes 54, 56, 70 and 75 are unmapped (silent).

Parameters (`DRUM_PARAMS`, 11): `level` -48..6 dB (-6); `kick_tune` -12..12 st (0); `kick_decay` 50..2000 ms (450); `snare_tune` -12..12 st (0); `snare_snappy` 0..100 % (60); `snare_decay` 50..1000 ms (220); `hat_decay` 20..500 ms (80); `open_hat_decay` 100..3000 ms (600); `tom_tune` -12..12 st (0); `tom_decay` 50..2000 ms (500); `cymbal_decay` 200..6000 ms (2000).

## Plugin folders

Source: `crates/vst3-host/src/scan.rs`, `crates/clap-host/src/scan.rs`. No caching; every scan re-walks folders; missing dirs skipped; symlinks followed; depth 8, max 4096 bundles, 100000 entries.

| OS | VST3 | CLAP |
|---|---|---|
| Windows | `%COMMONPROGRAMFILES%\VST3`, `%LOCALAPPDATA%\Programs\Common\VST3` | `%COMMONPROGRAMFILES%\CLAP`, `%LOCALAPPDATA%\Programs\Common\CLAP` |
| macOS | `~/Library/Audio/Plug-Ins/VST3`, `/Library/Audio/Plug-Ins/VST3` | `~/Library/Audio/Plug-Ins/CLAP`, `/Library/Audio/Plug-Ins/CLAP` |
| Linux/BSD | `~/.vst3`, `/usr/lib/vst3`, `/usr/local/lib/vst3` | `~/.clap`, `/usr/lib/clap`, `/usr/local/lib/clap` |

Extra folders: env `VST3_PATH` / `CLAP_PATH` (platform path separator, appended). Audio Units (`au:`) are macOS only (`crates/au-host`).

## Error recovery

Three classes (spec section 4.5-E). Strings are from source; the MCP wrapper returns them as `isError: true` text.

| Class | Typical real strings | Action |
|---|---|---|
| Fix the request (bad spec, wrong command or plugin name) | "unknown plugin `X`"; "`X` has no parameter `Y`"; "`plugin` required"; "`path` required"; "`db` or `delta_db` required"; "unknown kind `k`"; "unknown format `f`"; "`X` is not an instrument"; "only instrument tracks have an instrument"; "unknown field `k`: an instrument's parameters go in `params`..."; "`command` required". Unknown command id error text is UNVERIFIED (looked in: cmd/mod.rs, cli main.rs). | Correct the request and rerun; call `list_commands` with a `filter` to find the nearest command (substring match only, no suggestions). |
| Fix session state (track missing, transport playing) | "no track"; "unknown track"; "empty slot"; "all insert slots are in use"; "no bus named \"X\""; "a track named `X` already exists"; "the session has no tracks"; "nothing is selected"; "make an edit selection first"; "none of the requested tracks hold MIDI"; "{file} already exists: pass `replace: true` to replace it" | Re-read with `inspect_session`; run `transport.stop` before structural edits (source shows no hard block while playing, so this is precautionary; UNVERIFIED, looked in: transport.rs, mod.rs). Use `edit.undo` after bad edits. |
| Fix environment (not running, MCP not connected, file not writable) | MCP server fails to start or tools missing; a path outside a root returns a tool error; "no path yet: pass `path` (Save As)"; "cannot write `{format}` files"; `--connect` port unreachable. Exact path-outside-root string UNVERIFIED (looked in: docs/mcp.md, mcp.rs). | Go to setup (install `soundcraft-cli`, check `.mcp.json`, roots exist and include the target dir); fall back to writing a `.mid` file. |

Engine safety: `Engine::execute` catches escaped panics and restores the document (`AGENTS.md`). A failed `mix.instrument` changes nothing.

## Known limits

- No plugin sandbox: hosting is in-process, so a crashing third-party plugin can take down the host (`docs/plugin-parity.md`).
- Signed macOS builds refuse third-party VST3 (missing hardened-runtime entitlement, issues #153, #149) (`docs/plugin-parity.md`).
- No sidechain / key input in all three hosts (CLAP, VST3, AU).
- No live MIDI input (G-02). Recording is desktop-app only, not via headless MCP.
- Plugin discovery loads binaries from system folders and is not covered by automation roots.
- Hosted instruments (`clap:`, `vst3:`, `au:`) keep parameters in their own state; `mix.instrument_param` only works on built-ins (use `mix.insert_state` for raw state).
- `batch` max 1000 commands. Pre-alpha: commands and ids can change.

drum_synth map: CUSTOM
voice -> note (16 canonical voices; `unsupported` = no distinct sound in drum_synth, reject, do not fall back):
- kick: 36
- snare: 38
- clap: 39
- rim: unsupported (37 plays a clap)
- hat: 42
- open_hat: 46
- pedal_hat: 44 (plays as closed hat)
- ride: 51
- crash: 49
- tom_hi: 50
- tom_mid: 47
- tom_low: 45
- shaker: unsupported (70 is unmapped, silent)
- tambourine: unsupported (54 is unmapped, silent)
- cowbell: unsupported (56 is unmapped, silent)
- perc: unsupported (75 is unmapped, silent)
mcp args: ["mcp"]
