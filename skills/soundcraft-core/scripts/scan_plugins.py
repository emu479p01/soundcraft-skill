#!/usr/bin/env python3
"""Inventory plugin paths without opening binaries or loading plugins.

Python 3.9+ standard library only. Exit codes: 0 success (missing roots and
unsupported formats are warnings), 2 invalid arguments/roots, 1 I/O failure.
Directory symlinks are followed with resolved-path cycle and duplicate guards.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sys
from typing import Mapping, Optional
import unicodedata


REASON = "SoundCraft supports CLAP, VST3, AU only"
SUPPORTED = {".vst3": "vst3", ".clap": "clap", ".component": "au"}
UNSUPPORTED = {".vst": "vst2", ".aaxplugin": "aax", ".lv2": "lv2"}
CATEGORIES = (
    ("drum", ("drum", "kit", "sitala", "808", "perc")),
    ("synth", ("synth", "vital", "surge", "dexed", "serum", "ob-x", "odin", "helm", "tyrell")),
    ("eq", ("eq", "nova")),
    ("comp", ("comp", "limit", "glue")),
    ("reverb", ("reverb", "verb", "supermassive", "room", "plate")),
    ("delay", ("delay", "echo")),
    ("saturation", ("satur", "distort", "tape", "drive")),
)


def default_dirs(platform: str, env: Mapping[str, str], home: Path) -> list[tuple[Path, str]]:
    """Return spec section 5 roots, legacy warning roots, and CLAP_PATH.

    Split environment paths according to the requested OS, including when
    inspecting another platform's defaults on this host. Empty entries are ignored.
    """
    windows = platform.casefold() in ("win32", "windows", "cygwin")
    dirs = []
    if windows:
        # Environment keys are case insensitive on Windows, even for a plain dict.
        values = {key.casefold(): value for key, value in env.items()}
        programs = Path(values.get("programfiles") or "C:/Program Files")
        common = Path(values.get("commonprogramfiles") or programs / "Common Files")
        local = Path(values.get("localappdata") or home / "AppData/Local")
        dirs = [(common / "VST3", "vst3"), (common / "CLAP", "clap"),
                (local / "Programs/Common/VST3", "vst3"),
                (local / "Programs/Common/CLAP", "clap"),
                (programs / "VSTPlugins", "vst2"),
                (programs / "Steinberg/VstPlugins", "vst2"), (common / "VST2", "vst2")]
        clap_path = values.get("clap_path", "")
    elif platform.casefold() in ("darwin", "macos"):
        dirs = [(base / name, fmt)
                for base in (Path("/Library/Audio/Plug-Ins"), home / "Library/Audio/Plug-Ins")
                for name, fmt in (("VST3", "vst3"), ("CLAP", "clap"), ("Components", "au"))]
        clap_path = env.get("CLAP_PATH", "")
    else:
        dirs = [(home / ".vst3", "vst3"), (home / ".clap", "clap"),
                (Path("/usr/lib/vst3"), "vst3"), (Path("/usr/local/lib/vst3"), "vst3"),
                (Path("/usr/lib/clap"), "clap"), (Path("/usr/local/lib/clap"), "clap")]
        clap_path = env.get("CLAP_PATH", "")
    dirs.extend((Path(entry), "clap") for entry in clap_path.split(";" if windows else ":") if entry)
    return dirs


def categorize(name: str) -> str:
    """Use ordered keyword heuristics; preserve the original display name."""
    folded = "".join(char for char in unicodedata.normalize("NFKD", name.casefold())
                     if not unicodedata.combining(char))
    return next((category for category, words in CATEGORIES
                 if any(word in folded for word in words)), "other")


def _inside_bundle(path: Path) -> bool:
    return any(parent.suffix.casefold() in SUPPORTED or parent.suffix.casefold() in UNSUPPORTED
               for parent in path.parents)


def scan(dirs: list[tuple[Path, str]]) -> dict:
    """Walk files only, treating supported/unsupported bundle folders as leaves.

    Missing roots are reported. Other filesystem errors propagate so callers
    cannot mistake an unreadable tree for a complete inventory. DLLs are warnings
    only below explicitly designated vst2 roots. Paths retain their original text.
    """
    plugins, unsupported = {}, {}
    missing = set()
    visited = set()
    # Shallow roots first: overlapping roots cannot expose bundle internals.
    roots = sorted(((Path(path), fmt) for path, fmt in dirs),
                   key=lambda item: (len(item[0].parts), str(item[0]).casefold(), str(item[0]), item[1]))
    for root, root_format in roots:
        try:
            root.stat()
        except FileNotFoundError:
            missing.add(str(root))
            continue
        if not root.is_dir():
            raise ValueError(f"scan root is not a directory: {root}")
        pending = [root]
        while pending:
            path = pending.pop()
            resolved = path.resolve()
            if _inside_bundle(path) or _inside_bundle(resolved):
                continue
            suffix = path.suffix.casefold()
            fmt = SUPPORTED.get(suffix)
            unsupported_format = UNSUPPORTED.get(suffix)
            if suffix == ".dll" and root_format == "vst2":
                unsupported_format = "vst2"
            if fmt or unsupported_format:
                # Do not read any plugin content, even to check its validity.
                record = {"name": path.stem, "format": fmt or unsupported_format, "path": str(path)}
                if fmt:
                    record["category"] = categorize(path.stem)
                    plugins.setdefault(resolved, record)
                else:
                    record["reason"] = REASON
                    unsupported.setdefault(resolved, record)
                continue
            if not path.is_dir():
                continue
            identity = (resolved, root_format == "vst2")
            if identity in visited:
                continue
            visited.add(identity)
            with os.scandir(path) as entries:
                children = sorted((Path(entry.path) for entry in entries),
                                  key=lambda child: (child.name.casefold(), child.name))
            pending.extend(reversed(children))
    def order(record):
        return (record["name"].casefold(), record["name"], record["format"], record["path"])
    return {"plugins": sorted(plugins.values(), key=order),
            "unsupported": sorted(unsupported.values(), key=order),
            "missing_dirs": sorted(missing, key=lambda value: (value.casefold(), value))}


def _utf8_streams() -> None:
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            try:
                reconfigure(encoding="utf-8")
            except (ValueError, OSError):
                pass


def main(argv: Optional[list[str]] = None) -> int:
    _utf8_streams()
    parser = argparse.ArgumentParser(description="Inventory plugin files without loading or executing them.")
    parser.add_argument("--extra-dir", action="append", default=[], type=Path, help="additional scan root (repeatable)")
    parser.add_argument("--json", action="store_true", help="print scan results as JSON")
    parser.add_argument("--write-corpus", nargs="?", const=True, metavar="PATH",
                        help="write corpus (default: ~/.soundcraft-skills/plugins.json)")
    args = parser.parse_args(argv)
    try:
        home = Path.home()
        result = scan(default_dirs(sys.platform, os.environ, home) + [(p, "auto") for p in args.extra_dir])
        if args.write_corpus is not None:
            target = home / ".soundcraft-skills/plugins.json" if args.write_corpus is True else Path(args.write_corpus)
            corpus = {"scanned_at": datetime.now(timezone.utc).isoformat(), "platform": sys.platform, **result}
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(json.dumps(corpus, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            for category, _ in CATEGORIES + (("other", ()),):
                members = [p for p in result["plugins"] if p["category"] == category]
                if members:
                    print(f"{category}:")
                    for plugin in members:
                        print(f"  {plugin['name']} ({plugin['format']}): {plugin['path']}")
            if not result["plugins"]:
                print("No supported plugin files found.")
            for plugin in result["unsupported"]:
                print(f"WARN: {plugin['path']}: {plugin['reason']}")
            for directory in result["missing_dirs"]:
                print(f"WARN: missing directory: {directory}")
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except OSError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"error: unexpected {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
