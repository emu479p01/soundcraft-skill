---
name: plugins
description: Use when inventorying, comparing, recommending, installing by user action, or loading audio plugins in SoundCraft.
---

# Plugins

## When to use

- The user asks which plugins are available, what is unsupported, or what free plugin may suit a track.
- The user wants to use a third-party instrument or effect in SoundCraft.

## Workflow

1. **Preflight:** Confirm the request (inventory, recommendation, or load) and check the plugin reference. Never download, launch, or run an installer. Do not open a download page until after inventory and candidate selection.
2. **Read state:** Run `python ../soundcraft-core/scripts/scan_plugins.py --write-corpus` from this skill's directory. This inventories plugin files without opening or executing them and writes the default corpus under `~/.soundcraft-skills/plugins.json`. Use `--write-corpus PATH` to choose another corpus path and `--extra-dir DIR` for additional roots. Read the output and corpus; report entries by inferred category, missing directories, and every unsupported-format warning. A filename category is only a guess. Inventory names and paths are not SoundCraft plugin IDs and do not prove a plugin loads. For each `--extra-dir`, also check the user's declared contents/paths for `.dll` files: the current scan API does not include DLLs in extra roots in its unsupported list. Report these as unsupported VST2 candidates and disclose this inventory limitation; an empty unsupported list does not establish that the custom roots contain no unsupported plugins. If the user has not identified those contents, say that the custom-root DLL inventory remains unverified and ask for the paths or a manual file listing.
3. **Recommend:** Assess suitable plugins already present in the corpus first, against the user's task and criteria. Treat them as candidates only; verify an exact runtime ID with SoundCraft before claiming loadability. If none is a suitable verified candidate, compare catalog options using the vendor's official per-OS format availability and the user's OS/task; do not infer every listed format exists on every listed OS. Identify a free edition separately from optional paid editions. Then open the selected official product page, not an installer file, and let the user choose and perform any installation. Never download or run installers.
4. **After user installation:** Rescan with `python ../soundcraft-core/scripts/scan_plugins.py --write-corpus`. Before loading, check MCP and read `inspect_session`. Discover the plugin-list command using MCP `list_commands` (filter `plugins`) because `engine.vst3_plugins` and `engine.clap_plugins` are UNVERIFIED for MCP. If those commands are absent, do not treat disk inventory as a runtime list. Use the exact runtime plugin ID and format prefix returned by SoundCraft. Load an effect on an effect-capable track with `mix.insert`. For an instrument, create a uniquely named new instrument track with `track.new` by default, resolve its actual track ID from session state, and load with `mix.instrument` onto that track. Preserve current instruments and their clips. Replace an existing instrument only when the user explicitly requested or authorized that replacement; honor authorization already given and do not ask again. These command IDs are documented in `soundcraft-core/references/soundcraft-commands.md`. Re-read `inspect_session` and report whether the plugin actually loaded.
5. Before changing plugin parameters, read the ranges from a verified runtime source. Parameter-range lookup is UNVERIFIED; find a relevant command with `list_commands` first. Never invent a range query, setter, parameter range, or hosted-instrument parameter support. `mix.instrument_param` is for built-in instruments only. If runtime ranges or controls are unavailable, load without changing parameters and say so.
6. For an audio chain, use this starting order: **EQ → compressor → saturation → modulation → delay → reverb**. Adjust to the musical goal and avoid unnecessary processing. Re-read the session after changes. Limit generate/check/adjust cycles to three; report FAIL for an invalid operation or failed load, and WARN for unavailable runtime discovery or an unperformed audio check. State what loaded, the exact runtime ID, any unsupported warnings, and what was not verified.
7. If MCP is unavailable, deliver useful scan/recommendation results and, when music creation is in scope, a validated `.mid` handoff the user can import manually. MIDI is note data, not rendered or plugin-loaded audio. Give the absolute file path; never claim that audio was loaded, heard, or rendered if it was not.

Reply to the user in the language they wrote in.

## Style table

N/A — plugin choice depends on the requested instrument, effect, and installed host formats.

## Spec pattern

N/A — plugin inventory and loading do not define a MIDI spec.

## Checks

- Read the scan output after every scan; distinguish supported candidates from unsupported formats and missing folders.
- Confirm exact runtime IDs and successful load from SoundCraft's response/session state. A plugin file on disk is not proof of either.
- Report whether any audio was actually rendered and measured. A `.mid` handoff is not audio.

## Limits

- `scan_plugins.py --write-corpus` writes an inventory corpus; `--json` prints results as JSON. It never loads a plugin. See `python ../soundcraft-core/scripts/scan_plugins.py --help` for options.
- Unsupported-format reporting is limited by the scanner's configured roots. In particular, `.dll` files under `--extra-dir` roots are not inventoried as unsupported by the current API; manually inspect and report those paths as unsupported VST2 candidates, or state that the custom-root check is incomplete. Do not describe the scan as a complete unsupported-plugin inventory.
- The scanner infers categories from filenames and can report formats it does not support. Its inventory is not a registry of host runtime IDs.
- SoundCraft is pre-alpha. Check command availability with `list_commands`; never assume unverified plugin discovery, range lookup, or hosted-instrument controls exist.
- Third-party plugins run in process and may crash the host. Consult the current SoundCraft command reference for platform-specific hosting limits.
- Free-plugin examples with concise verification notes are in [references/free-plugins.md](references/free-plugins.md). Availability can change; verify the official vendor page before recommending.

## Related skills

Use `soundcraft-setup` for MCP setup and file access, `chords` or `drums` for MIDI composition, and `sound-design` for patch design.
