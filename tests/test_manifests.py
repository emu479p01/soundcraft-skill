# Schema sources checked 2026-10-25; these are contract checks, not native loaders.
# Claude: https://code.claude.com/docs/en/plugins-reference
# .claude-plugin/plugin.json requires name; version/author/license are optional.
# Component paths start ./ and resolve from plugin root; .mcp.json is discovered.
# Claude marketplace: https://code.claude.com/docs/en/plugin-marketplaces
# Requires name, owner (name), plugins; each entry requires name and source.
# Relative source ./ resolves from the marketplace root (this repository).
# Codex: https://developers.openai.com/plugins/build/plugins
# (redirect from https://developers.openai.com/codex/plugins/build).
# Supported compatibility scaffold: .codex-plugin/plugin.json, skills: ./skills/,
# mcpServers: ./.mcp.json; the latter has a top-level mcpServers object.
# Repo marketplace: .agents/plugins/marketplace.json with name and plugins;
# entries use name and source: {source: local, path: ./}, from marketplace root.
# Local installed compatibility example: remotion/4.0.534/.codex-plugin/plugin.json.
# Antigravity: https://antigravity.google/docs/plugins
# Root plugin.json requires name; description is optional; no other keys allowed.
# skills/ and mcp_config.json are conventionally discovered.
# https://antigravity.google/docs/mcp: mcpServers map, local command and args;
# global path ~/.gemini/config/mcp_config.json.
# UNVERIFIED: native Codex overlay coexistence with Antigravity root plugin.json;
# schema/shape tests do not establish runtime loading or model frontmatter support.
"""Repository manifest contracts, without installing any plugin."""
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
MANIFESTS = (
    '.claude-plugin/plugin.json', '.claude-plugin/marketplace.json', '.mcp.json',
    '.codex-plugin/plugin.json', '.agents/plugins/marketplace.json',
    'plugin.json', 'mcp_config.json',
)


class ManifestTests(unittest.TestCase):
    def read(self, name):
        path = ROOT / name
        self.assertTrue(path.is_file(), 'Missing manifest: ' + name)
        return json.loads(path.read_text(encoding='utf-8'))

    def test_all_json_parses(self):
        for name in MANIFESTS:
            with self.subTest(name=name):
                self.assertIsInstance(self.read(name), dict)

    def test_plugin_identity_and_supported_metadata(self):
        for name in ('.claude-plugin/plugin.json', '.codex-plugin/plugin.json'):
            with self.subTest(name=name):
                data = self.read(name)
                self.assertEqual(data['name'], 'soundcraft-skills')
                self.assertEqual(data['version'], '0.1.0')
                self.assertEqual(data['author']['name'], 'Chaiyaporn Santangjai')
                self.assertEqual(data['license'], 'MIT')
        antigravity = self.read('plugin.json')
        self.assertEqual(antigravity['name'], 'soundcraft-skills')
        self.assertEqual(set(antigravity), {'name', 'description'})

    def test_mcp_matches_canonical_and_command_reference(self):
        self.assertTrue((ROOT / 'install.py').is_file(), 'The fallback installer is missing')
        import install
        self.assertEqual(install.MCP_SERVER, {'command': 'soundcraft-cli', 'args': ['mcp']})
        reference = (ROOT / 'skills/soundcraft-core/references/soundcraft-commands.md').read_text(encoding='utf-8')
        args_line = next(line for line in reference.splitlines() if line.startswith('mcp args:'))
        self.assertEqual(install.MCP_SERVER['args'], json.loads(args_line.split(':', 1)[1]))
        for name in ('.mcp.json', 'mcp_config.json'):
            with self.subTest(name=name):
                self.assertEqual(self.read(name)['mcpServers'], {'soundcraft': install.MCP_SERVER})

    def test_codex_compatibility_paths(self):
        data = self.read('.codex-plugin/plugin.json')
        self.assertEqual(data['skills'], './skills/')
        self.assertEqual(data['mcpServers'], './.mcp.json')

    def test_marketplace_sources_resolve_to_root(self):
        claude = self.read('.claude-plugin/marketplace.json')
        self.assertEqual(claude['owner']['name'], 'Chaiyaporn Santangjai')
        self.assertEqual(claude['plugins'][0]['source'], './')
        codex = self.read('.agents/plugins/marketplace.json')
        self.assertEqual(codex['plugins'][0]['source'], {'source': 'local', 'path': './'})
        self.assertTrue(codex['interface']['displayName'])
        for data in (claude, codex):
            self.assertTrue(data['name'])
            self.assertEqual(len(data['plugins']), 1)
            self.assertEqual(data['plugins'][0]['name'], 'soundcraft-skills')
