# SoundCraft Skills

Eight practical music-production skills and offline MIDI tools for SoundCraft: session setup, chords, drums, sound design, plugin guidance, music theory, Thai musical flavor, and the shared SoundCraft workflow.

The skills help an agent turn a musical request into a reviewed MIDI sketch, guide SoundCraft actions when its MCP server is available, and explain manual alternatives. MIDI carries notes; it does not contain rendered audio, samples, or instrument patches.

## Requirements

- Python 3.9 or newer. Scripts and fallback installer use only the Python standard library.
- SoundCraft and `soundcraft-cli` are optional for local MIDI generation. SoundCraft is required for DAW integration and audio bounce.
- A supported agent harness: Claude Code, Codex, or Antigravity. Native Codex and Antigravity plugin coexistence has not been verified; see [harness notes](docs/harness-notes.md).

## Install

Published repository URL: **PLACEHOLDER — replace with the actual GitHub owner/repository URL before publication.** No remote is configured for this checkout.

### Claude Code

```text
/plugin marketplace add <local-repository-path-or-published-repository-url>
/plugin install soundcraft-skills@soundcraft-skills
```

### Codex and Antigravity fallback installer

Preview first; these commands do not write files:

```bash
python install.py --codex --dry-run
python install.py --antigravity --dry-run
```

After reviewing proposed copies and MCP config edits, apply only to the intended host:

```bash
python install.py --codex
python install.py --antigravity
```

`--all` targets both fallback hosts; `--link` requests links with copy fallback. The installer does not install SoundCraft or Python, change Claude configuration, grant MCP file roots, or remove conflicts. Resolve conflicts manually. See [harness notes](docs/harness-notes.md).

### SoundCraft CLI and file access

The repository MCP manifests launch `soundcraft-cli mcp` and grant no file roots by default. Configure only explicitly approved workspace roots in the chosen harness, following its documentation and the [setup skill](skills/soundcraft-setup/SKILL.md).

On one Windows machine the real CLI was found at `C:\Program Files\SoundCraft\soundcraft-cli.exe` (version 0.12.1), but it was not on PATH. Use that absolute executable path or configure PATH yourself if appropriate. This local observation does not imply the CLI is installed or verified on other machines or versions.

## Local MIDI example

Generate the included lo-fi example without installing anything:

```bash
python skills/soundcraft-core/scripts/make_midi.py skills/soundcraft-core/examples/lofi-sketch.json --out out/lofi.mid
```

The result is a MIDI file. Import it into a DAW with a suitable instrument to hear it. The optional SoundCraft MCP path can import MIDI and assign an available instrument when configured and authorized. Review results before relying on them.

## Example requests

- “Make a relaxed four-bar lo-fi chord loop in D minor at 82 BPM, and save a MIDI file I can import.”
- “Add a restrained pop drum groove under these chords; show me the note pattern and approximations.”
- “Help me make the synth darker using controls this SoundCraft build supports.”
- “Analyze this MIDI for key and chords, and explain uncertain results plainly.”
- “Suggest a Thai-inspired melodic direction, but ask me for a regional or musical reference before claiming cultural fidelity.”
- “List plugins already in my inventory and recommend an option without downloading or installing anything.”

The skills should explain what they did, identify approximations or unavailable access, and give artifact paths and next steps in the user's language. They ask before software installation or harness configuration changes, honoring consent already given for the same scope.

## Status and roadmap

Phase 1 contains eight skills: `soundcraft-core`, `soundcraft-setup`, `chords`, `drums`, `plugins`, `sound-design`, `theory-coach`, and `thai-flavor`.

Phase 2 is planned to add bassline/melody, groove humanization, session templates, and reference briefs. Phase 3 is planned to add song sketches, mix assistance, export/delivery, and producer next-step guidance. These are roadmap items, not current capabilities.

## License and credits

MIT licensed; see [LICENSE](LICENSE). Idea sources and license notes are in [CREDITS.md](CREDITS.md).
