# Harness validation notes

Checked on 2026-10-25 in the existing `feat/phase1` checkout. Package identity is
`soundcraft-skills`, version `0.1.0`, author Chaiyaporn Santangjai, MIT license.
Copyright (c) 2026 Chaiyaporn Santangjai; see [LICENSE](../LICENSE).

## Manifest contracts

- [Claude manifest reference](https://code.claude.com/docs/en/plugins-reference)
  and [marketplace reference](https://code.claude.com/docs/en/plugin-marketplaces):
  metadata lives in `.claude-plugin/plugin.json`; the marketplace's `./` source
  points to this repository root. Skills and `.mcp.json` use conventional discovery.
- [Codex packaging reference](https://developers.openai.com/plugins/build/plugins)
  (redirected from `https://developers.openai.com/codex/plugins/build`): retain the
  supported `.codex-plugin/plugin.json` compatibility scaffold with
  `skills: "./skills/"` and `mcpServers: "./.mcp.json"`. The repo marketplace uses
  `source: {"source": "local", "path": "./"}`. The locally installed Remotion
  `4.0.534` plugin also provides a compatibility manifest example. This project
  does not claim to implement the portable Agent Plugins root format.
- [Antigravity plugins](https://antigravity.google/docs/plugins): the current
  root `plugin.json` schema allows only `name` and `description`. It requires
  `name` and forbids additional properties. Version, author, license, and a
  `$schema` property are therefore omitted there. Version agreement is tested
  only between Claude and Codex. Copyright and licensing remain in LICENSE/docs.
- [Antigravity MCP](https://antigravity.google/docs/mcp): the fallback JSON target
  is `~/.gemini/config/mcp_config.json`, using an `mcpServers` map.

`tests/test_manifests.py` records source URLs and checks the local contracts.
Both MCP files match the single installer `MCP_SERVER` constant:
`{"command": "soundcraft-cli", "args": ["mcp"]}`. The args also match the final
`mcp args:` line in the SoundCraft command reference.

## Native checks and their limits

`claude --version` returned `2.1.310 (Claude Code)`. Both commands exited 0:

```text
claude plugin validate .
claude plugin validate .claude-plugin/plugin.json
```

Both ended with `Validation passed`. The validator separately reported
`README_MISSING` (at the time, a plugin directory submission refusal) and `ICON_MISSING`
(a plugin directory warning). These do not fail its default validation profile.
The directory submission profile, policy review, skills installation, and MCP
execution were not tested. README is now present; rerun validation if directory
submission is intended.
An initial marketplace description warning was fixed before the final checks.

`codex --version` returned `codex-cli 0.164.0`. A native parser probe used the
installed `codex.exe app-server --stdio`, without starting an agent or inference.
First, `app-server generate-json-schema --out <temporary schemas>` exited 0;
its `InitializeParams` and `SkillsListParams` schemas supplied the request shapes.
The fixture was `<temporary project>/.agents/skills/model-probe/SKILL.md`:

```yaml
---
name: model-probe
description: Temporary frontmatter tolerance probe.
model: sonnet
---
```

The local JSON-RPC exchange was:

```json
{"id":1,"method":"initialize","params":{"clientInfo":{"name":"soundcraft-frontmatter-probe","version":"0.1.0"}}}
{"method":"initialized","params":{}}
{"id":2,"method":"skills/list","params":{"cwds":["<temporary project>"],"forceReload":true}}
```

The final filtered result was `rpc_error: null`, one `model-probe` skill with
`scope: "repo"`, `enabled: true`, `pluginId: null`, and `errors: []`. Initialization
confirmed the temporary CODEX_HOME. Stderr warned, `Refusing to create helper
binaries under temporary dir`; it did not prevent skill listing. This establishes
frontmatter parser tolerance in this installed build only. It does not establish
that `model: sonnet` selects a model, or that native plugin loading works.

All fixture/config/schema writes were under a temporary directory. The probe
redirected CODEX_HOME, HOME, USERPROFILE, APPDATA, LOCALAPPDATA, and XDG_CONFIG_HOME,
and removed OPENAI_API_KEY and CODEX_API_KEY from its child environment. The loader
also listed existing user skills through the OS-resolved home; these were read
only and were not changed. The server was terminated before temporary cleanup.

`Get-Command agy -ErrorAction SilentlyContinue` found no Antigravity CLI, so its
frontmatter and native plugin checks are unavailable. Production skill
frontmatter remains without `model:` because both hosts have not been verified.
Native coexistence of the Codex compatibility overlay with Antigravity's root
manifest is **unverified**. JSON shape checks do not prove native support.

## Fallback installer verification and behavior

The original installer unit tests (`tests/test_install.py`) use a fake repository
with a fake `chords` skill and temporary homes. Separately, the final integration
probe (`fallback-install-probe.json` in the local review artifacts) copied this
repository's actual eight skills into both temporary Codex and Antigravity fake
homes and confirmed the core CLI was present. It exposed setup's missing
`../../docs/harness-notes.md` link in both copies, plus source-only installer
paths that could not work in a copied installation.

The final correction adds `tests/test_installed_guidance.py`: it copies the actual
eight-skill package into two separate temporary fake homes and checks all relative
Markdown file links and required runtime recovery guidance. Setup now links to
`../soundcraft-core/references/harness-setup.md`, included in both copies; its
runtime links resolve in both layouts. The source-checkout-only installer route
requires a verified user-provided absolute checkout path. Installed users can
recover MCP manually without that checkout. These are package-copy/link checks,
not native host loading or a real-user installation. No real user config,
installed skills, marketplace registration, or software installation was changed.
No push or publication was performed.

`install(targets, home, repo, dry_run=False, link=False)` accepts Codex and
Antigravity, and the CLI exposes `--codex`, `--antigravity`, `--all`, `--dry-run`,
and `--link`. No target prints help and Claude marketplace instructions. The
installer only prints Claude instructions; it never registers or installs Claude.
Use `--dry-run` first and apply only after authorizing changes to the chosen home.

Config/skill conflicts are preflighted across all requested targets before writes.
Different existing skills or SoundCraft server entries raise an actionable
`ValueError` (CLI exit 1); move or reconcile those entries explicitly before
rerunning. No arbitrary destination is deleted. Identical copies and correct
links remain unchanged. Link creation failure warns and copies only if the
destination is still absent. Source links and redirected destination parents
are rejected. Updates to a different installed skill require manual reconciliation.

Unchanged configs create no backup. Before changed existing configs, backups use
`<file>.bak-YYYYmmddHHMMSS`; exclusive creation adds `-1`, `-2`, etc. on collisions.
Codex TOML is append-only and preserves unrelated original bytes/newlines. This
is a conservative text editor, not a general TOML parser: ambiguous existing MCP
syntax may require manual reconciliation, even if semantically equivalent.
Any triple-quote marker (`"""` or `'''`) is refused during preflight, including
markers in comments or ordinary strings. Multiline TOML requires manual setup;
this refusal occurs before any skill copies, backups, or config writes.
Antigravity preserves unrelated JSON values, reformats only on change, and rejects
duplicate keys. Filesystem failures may leave completed skill copies; installation
is not a cross-file transaction. A config backup failure prevents that config edit.

Changed configs are written to exclusive sibling temporary files, flushed, and
atomically replaced after another identity/content and parent-containment check.
Detected replacements, edits, newly appeared configs, and redirected parents are
refused; the final replacement never writes through a substituted config symlink.
POSIX commits use a directory descriptor and no-follow opens; Windows commits
hold native directory handles denying ancestor renames until replacement finishes.
Temporary siblings are removed on failure, and existing-config backups precede
replacement. Atomic replacement creates a new file, so original file identity and
custom permissions/metadata are not preserved (POSIX siblings start with mode 0600).
These checks do not provide a filesystem transaction or serialize unrelated
writers: another writer can still race the final content check and replacement.

The Task 9 record reported Python 3.12.14. The final correction's actual runtime
reports Python 3.14.7; an actual Python 3.9 runtime was not tested. Implementation
and tests use standard-library APIs available in Python 3.9; a Python 3.9 grammar
parse checks source syntax only, not execution on that older interpreter.
Original validation: 25 Task 9 tests and 167 full-suite tests passed with no skips.
The Task 9 fix adds regressions for multiline conflicts, post-backup substitutions,
late config/parent links, atomic replacement failure/cleanup, and new config paths.
Fix-round focused validation: 33 installer/manifest tests passed in 0.510 seconds.
The required full-suite command was run once after the fixes:
`python -m unittest discover -s tests -t .` -> 175 tests passed in 6.074 seconds,
exit 0, no skips. Detailed RED/GREEN evidence is in the Task 9 workspace report.
Windows handle behavior is tested natively; the POSIX branch is source-reviewed
but has not been executed on a POSIX host in this session.

## Task 19 real CLI smoke evidence

On 2026-10-25, SoundCraft CLI 0.12.1 was exercised in three isolated headless sessions using the installed Windows executable. The recorded method was real import, instrument assignment, and bounce; `out/live-smoke-12e28s38/results.json` and the accompanying raw logs are the evidence. The CLI was not on PATH. The generated WAVs are ignored local artifacts and are not committed.

| Case | Instrument/session result | WAV bytes | Duration | LUFS | Peak dBFS | True peak dBFS |
|---|---|---:|---:|---:|---:|---:|
| Setup | Initial session | 2,304,104 | 8.000 s | -22.982 | -13.136 | -13.125 |
| Chords | Track “Pop Chords”, ID 1, `subtractive_synth` | 2,468,672 | 8.571 s | -22.733 | -13.602 | -13.601 |
| Drums | Track “Pop Drums”, ID 1, `drum_synth` | 2,468,996 | 8.573 s | -27.256 | -7.266 | -7.077 |

All three WAVs were nonzero in size, had finite measured peaks, and remained below 0 dBFS (no clipping). This is evidence for the real CLI's isolated import/instrument/bounce flow on this machine and version only. At that time, MCP transport had not been tested; a separate transient stdio MCP smoke is recorded below. This does not test integration through a native agent harness, third-party hosting, listening quality, or cultural fidelity. Keep those explicitly untested. No software installation or harness configuration change was performed for this smoke run.

## Final correction verification (2026-10-25)

Fresh controller checks after the final fix wave: 195 tests passed on Python
3.12.14; all 8 skills passed `python -B tools/lint_skills.py`; Claude validation
passed with the known `ICON_MISSING` warning. These are the fresh final-wave
results. Earlier worker results on Python 3.14.7 (including source/targeted
checks) are historical and distinct; they are not the controller's fresh run.

A transient stdio MCP server smoke passed with SoundCraft CLI 0.12.1 and protocol
`2024-11-05`. It used explicit workspace read and write roots. `list_commands`,
`inspect_session`, MIDI import, instrument assignment, and an 8.0 s bounce all
succeeded; measured peak was -13.136 dBFS and integrated loudness was -22.982
LUFS. Evidence is `out/live-smoke-12e28s38/mcp-results.json` and
`mcp-transcript.json`. The transient server was terminated after the check; no
permanent MCP registration or configuration was changed. This proves a direct
stdio MCP run only, not native harness loading/coexistence, third-party hosting,
or listening quality.

The same installed SoundCraft CLI 0.12.1 import probe showed that the writer's
four-bar EOT boundary at tick 7680 was present, but the importer ignored silent
EOT tails: sparse four-bar material intended for 8.0 s became a 294000-sample,
6.125 s clip, and an all-rest file created no track. The CLI's actual
`describe` output exposed `edit.trim_clip` parameters
`{clip: id, start?: position, end?: position}`; edges move in the current edit
mode. In an isolated verified Slip-mode test, extending the actual new clip
with `end: {seconds: 8.0}` changed its end from 294000 to 384000 samples at
48 kHz while all four notes remained. This behavior is verified only for that
clip and mode. Other modes and hosts were not tested. Evidence:
`duration-import-results.json` and `trim-results.json` under
`out/live-smoke-12e28s38`.

The earlier Claude validator results and Codex parser probe above remain limited to the installed builds described there. They do not establish native Codex or Antigravity plugin coexistence or verified installation. Actual eight-skill temporary-home copies were tested separately as described above; native host loading of that package and real-user installation remain untested. The isolated SoundCraft 0.12.1 probe establishes the EOT import limitation described above, not general host import/loop behavior. `README_MISSING` is resolved by adding this repository README. `ICON_MISSING` remains a directory-submission warning; no icon-readiness claim is made.
