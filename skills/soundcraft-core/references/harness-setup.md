# Runtime harness setup and MCP recovery

This reference ships with the skills. Copied installations contain sibling skill
folders, including core scripts; repository-root docs, manifests and `install.py`
are not included. Native Codex/Antigravity plugin loading and coexistence remain
unverified. A successful copy or manifest check does not prove a working MCP connection.

## Recover MCP from an installed skill

Check `soundcraft-cli --version` first. If the harness cannot find it on PATH,
use the verified absolute executable path in its server command. Before editing
configuration, show the proposed changes and obtain authorization for that scope;
existing consent for the same action suffices. Back up existing config, preserve
other servers/settings, and reconcile an existing SoundCraft entry rather than
adding duplicates. No repository checkout or installer is needed for these steps.

- **Claude Code:** manual registration from a terminal is
  `claude mcp add soundcraft -- soundcraft-cli mcp`. Optional `--demo` is not
  required. Inspect the active registration if a SoundCraft server already exists.
- **Codex:** merge the following server table into `~/.codex/config.toml`:

  ```toml
  [mcp_servers.soundcraft]
  command = "soundcraft-cli"
  args = ["mcp"]
  ```

- **Antigravity:** merge the server into the existing `mcpServers` map in
  `~/.gemini/config/mcp_config.json` (this is a minimal complete config example):

  ```json
  {"mcpServers": {"soundcraft": {"command": "soundcraft-cli", "args": ["mcp"]}}}
  ```

Reconnect/restart the chosen harness connection, then call `list_commands`.
Failure still permits local MIDI generation with the installed core scripts and
manual DAW import. Report connection and audio checks separately.

Args `["mcp"]` grant **no file read/write roots**. For import, bounce or preset
access, obtain approval for an existing absolute work directory and add only the
needed `--automation-read-root` / `--automation-write-root` args, each followed by
that directory. Follow [setup's file-access and smoke workflow](../../soundcraft-setup/SKILL.md)
for examples, desktop `--connect` restrictions, state checks and measurements.

## Source-checkout-only installer or marketplace setup

Use this route only when the user supplies an actual source checkout. Obtain its
real user-provided absolute path and verify `install.py` exists there. Replace
`<checkout>` below with that confirmed path before running; the placeholder is
not a command to execute literally. Never derive it from an installed skill path.
Use `python3` instead of `python` where that is the verified Python ≥3.9 command.

```text
python "<checkout>/install.py" --codex --dry-run
python "<checkout>/install.py" --codex
python "<checkout>/install.py" --antigravity --dry-run
python "<checkout>/install.py" --antigravity
```

Preview only the requested host, review its changes, then apply within the
authorized scope. `--all` targets both hosts; `--link` requests links with copy
fallback. Copies go to `~/.agents/skills` or `~/.gemini/config/skills` respectively.
Changed configs are backed up; conflicting skills/server entries require manual
reconciliation. The installer does not install Python/SoundCraft or grant file roots.

Claude's source-checkout marketplace route, from its command UI, is
`/plugin marketplace add "<checkout>"`, then
`/plugin install soundcraft-skills@soundcraft-skills`; it supplies `.mcp.json`.
Use the same confirmed checkout substitution and authorization rules. Without a
checkout, use the manual MCP steps above with the already installed skills.
