---
name: soundcraft-setup
description: Use when SoundCraft or Python is missing, MCP cannot connect, file-root permissions block import or bounce, or a first-run audio smoke test is needed.
---

## When to use

Diagnose prerequisites, configure the user's chosen harness with permission, and verify sound. Read [command contracts and access rules](../soundcraft-core/references/soundcraft-commands.md) and [harness installation notes](../../docs/harness-notes.md) for the relevant host. Native Codex/Antigravity plugin coexistence remains unverified; manifest validation is not an installation test.

## Workflow

Follow these four steps in this order:

1. `soundcraft-cli --version` → missing: explain how to install per OS + Releases link, proceed once the user confirms
2. Python 3 → missing: recommend `winget install Python.Python.3` / `brew install python` / the package manager, run when the user permits
3. MCP `list_commands` → fails: show the setup steps for the harness in use, or recommend `install.py`
4. Smoke test: C–G–Am–F, 4 bars → import → `bounce_mix` → report peak/LUFS (peak > -inf = pass)

**Steps 1–2: prerequisites.** On Windows, macOS or Linux, use the matching OS/architecture asset and its instructions from [SoundCraft Releases](https://github.com/storytold/soundcraft/releases); confirm `soundcraft-cli` is on PATH. Do not invent package names or assume a release asset exists for every platform. Check `python --version` (or `python3 --version` on macOS/Linux); require ≥3.9, stdlib only. Propose the exact software/source and scope before installation. Existing consent for that same action suffices; otherwise wait for explicit authorization. Missing prerequisites leave setup incomplete; explain the next step rather than claiming success.

**Step 3: harness and file access.** Run commands from this skill's directory. Before installing skills or editing config, present the proposed changes and obtain explicit authorization, respecting consent already granted. These are instructions to apply only within that authorization:

- Claude Code: from the host's command UI, `/plugin marketplace add "/absolute/path/to/soundcraft-skill"`, then `/plugin install soundcraft-skills@soundcraft-skills`. The package supplies `.mcp.json`. For manual registration instead, the documented CLI form is `claude mcp add soundcraft -- soundcraft-cli mcp --demo`; `--demo` is optional. Reconcile an existing registration rather than adding duplicates.
- Codex fallback: preview `python ../../install.py --codex --dry-run`, review, then apply `python ../../install.py --codex` after authorization. It copies skills to `~/.agents/skills` and merges `[mcp_servers.soundcraft]` in `~/.codex/config.toml` with `command = "soundcraft-cli"`, `args = ["mcp"]`.
- Antigravity fallback: preview `python ../../install.py --antigravity --dry-run`, then authorized apply without `--dry-run`. It copies skills to `~/.gemini/config/skills` and merges `mcpServers.soundcraft` in `~/.gemini/config/mcp_config.json`. Manual setup uses `command: "soundcraft-cli"`, `args: ["mcp"]` in that entry. The repository's `plugin.json`/`mcp_config.json` are the native packaging scaffold; see harness notes for verified limits.

`install.py --all` targets both fallback hosts; `--link` requests links with copy fallback. Existing changed configs are backed up; conflicting skills/server entries require manual reconciliation, never deletion by assumption. The installer does not install SoundCraft/Python or grant file roots. Refresh/restart the chosen harness connection and retry `list_commands` after setup.

Canonical manifests launch with args `["mcp"]`: **no read roots and no write roots**, so import, bounce and preset file access are denied. First choose an existing working directory with the user. For example, if the approved existing folder is `C:/Music/Work`, propose the server's full argument array:

```json
["mcp", "--automation-read-root", "C:/Music/Work", "--automation-write-root", "C:/Music/Work"]
```

On macOS/Linux substitute the approved absolute existing directory, such as `/Users/alex/Music/Work` or `/home/alex/Music/Work`. After authorization, update only that server's args in the host locations above (Claude: active `.mcp.json` registration), reconnect, and retry. Read/write roots are separate and repeatable; grant only needed directories, never assume whole-drive access. Use absolute input/output paths inside the corresponding roots; resolved links outside them fail. If access is denied, inspect the active server args and resolved paths before retrying. Successful plugin registration is not evidence that imports, bounces or preset writes are enabled.

Desktop alternative: launch `soundcraft --control 7801`, then connect using `soundcraft-cli mcp --connect 7801`. **`--connect` cannot be combined with automation-root flags**; it is a separate desktop access mode, not a root grant. Check its actual file-operation results; never assume access from connection success.

**Step 4: preflight → read state → act → re-read.** Call `list_commands`, then `inspect_session` and preserve existing tracks/clips. For any reference entry marked UNVERIFIED, find it with `list_commands` first. Range-query tooling is UNVERIFIED: discover first, never invent a query command; this smoke test needs no parameter edits. If an empty engine needs initialization, use `new_session` only when it will not replace existing work. Generate the spec below locally. Check the note summary, import via `execute` command `file.import_midi` with `{path: absoluteMidiPath}`, then re-read `inspect_session`. Identify the actual new tracks from the import response and state; never assume the requested name or an ID. Attach verified `subtractive_synth` with `mix.instrument {track: actualTrack, plugin: "subtractive_synth"}` only when that track is an instrument track. If its kind is incompatible, discover supported routing/conversion first and report a blocker if unavailable. Re-read after every change. Stop transport before structural changes when needed.

With approved write access, call `bounce_mix {path: absoluteWavPath, format: "wav"}` over the four-bar span and report returned peak dBFS and integrated LUFS. Finite peak > -inf verifies sound; peak >0 dBFS is a separate clipping FAIL. Silence, invalid MIDI, import or instrument errors are FAIL; unavailable audio measurement is WARN and smoke verification remains incomplete. Limit generate → measure → adjust to 3 rounds total; stop and ask about unresolved FAILs. On unavailable MCP or denied paths, still generate the local `.mid` if Python works, give its absolute path for manual drag/import, and explain what remains untested. For scan-only diagnosis, report findings without creating an unrelated MIDI file. Finish with plain language: what changed, chosen values/reasons, file locations, peak/LUFS or unavailable measurements, and next step.

Reply to the user in the language they wrote in.

## Style table

N/A — setup uses a neutral four-bar smoke progression rather than a genre arrangement.

## Spec pattern

Save as `smoke.json` in the approved working directory:

```json
{
  "bpm": 120, "time_signature": [4, 4], "key": "C major",
  "output": "smoke.mid",
  "tracks": [{"name": "Setup Smoke", "type": "chords",
    "progression": ["C", "G", "Am", "F"], "chord_length": "1bar",
    "voicing": "close", "octave": 4, "rhythm": "pad", "velocity": 80}]
}
```

From this skill directory: `python ../soundcraft-core/scripts/make_midi.py "/absolute/work/smoke.json" --json` (substitute the real path). Relative `output` resolves beside the spec. This creates four bars of notes without SoundCraft. See `soundcraft-core` for CLI options/exit codes and the schema table.

## Checks

Confirm Python ≥3.9, CLI version, responding MCP, actual imported tracks/instrument, and measured audio separately. At 120 BPM in 4/4 the four bars last eight seconds before release tails. Use actual returned measurements; a generated `.mid` alone cannot prove audible output. Do not overwrite existing MIDI/WAV/preset files without permission; choose a fresh filename and update the spec/output path when needed.

## Limits

No automatic plugin downloads/installers. Every software install or harness config edit needs explicit authorization for its scope. Headless MCP has no window/audio device but supports offline bounce; `--demo` is not required. If Python is absent and installation is not authorized, provide the JSON and pending generation command, not a claim that a MIDI file exists.

## Related skills

Use `soundcraft-core` for script interfaces and offline export, `plugins` for owned-plugin discovery, and `chords`/`drums` once setup works.

<!-- ideas: Korben00/ableton-producer-skills (MIT), Goldwaterfung/Stratawright (MIT); preflight, state checks and measured verification, rewritten for SoundCraft. -->
