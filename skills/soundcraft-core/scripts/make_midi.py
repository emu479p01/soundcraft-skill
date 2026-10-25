#!/usr/bin/env python3
"""Render a SoundCraft JSON song spec to a Standard MIDI File plus a per-bar summary.

Usage: python make_midi.py SPEC.json [--out PATH] [--json]
  SPEC.json  the spec file, or - to read it from stdin
  --out      output .mid path (overrides the spec's "output"; relative to the cwd)
  --json     print the summary as JSON instead of text

A relative "output" in the spec is resolved next to the spec file. With neither,
the output is <spec stem>.mid next to the spec (out.mid in the cwd for stdin).

Exit codes: 0 written, 2 invalid spec (nothing written), 1 I/O or unexpected error.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).resolve().parent))

from scmidi.midi_writer import write_smf  # noqa: E402
from scmidi.render import render_detailed  # noqa: E402
from scmidi.spec import SpecError, validate_spec  # noqa: E402


def _utf8_streams() -> None:
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            try:
                reconfigure(encoding="utf-8")
            except (ValueError, OSError):
                pass


def _load(arg: str) -> tuple[object, Optional[Path]]:
    if arg == "-":
        data, spec_file = sys.stdin.buffer.read(), None
    else:
        spec_file = Path(arg)
        data = spec_file.read_bytes()
    try:
        return json.loads(data.decode("utf-8-sig")), spec_file
    except UnicodeDecodeError as e:
        raise SpecError("spec", f"is not valid UTF-8 text ({e})") from None
    except json.JSONDecodeError as e:
        raise SpecError("spec", f"invalid JSON at line {e.lineno} column {e.colno}: "
                                f"{e.msg}") from None


def _output_path(out_arg: Optional[str], raw: dict, spec: dict,
                 spec_file: Optional[Path]) -> Path:
    if out_arg:
        return Path(out_arg).absolute()
    base = spec_file.absolute().parent if spec_file else Path.cwd()
    if "output" in raw:
        out = Path(spec["output"])
        return out if out.is_absolute() else base / out
    return base / (f"{spec_file.stem}.mid" if spec_file else spec["output"])


def main(argv: Optional[list[str]] = None) -> int:
    _utf8_streams()
    parser = argparse.ArgumentParser(description="Render a JSON song spec to a .mid file.")
    parser.add_argument("spec", help="spec JSON file, or - for stdin")
    parser.add_argument("--out", help="output .mid path (overrides the spec's output)")
    parser.add_argument("--json", action="store_true", help="print the summary as JSON")
    args = parser.parse_args(argv)
    try:
        raw, spec_file = _load(args.spec)
        spec = validate_spec(raw)
        song, lines, details = render_detailed(spec)
        out = _output_path(args.out, raw, spec, spec_file)
        write_smf(song, out)
        out = out.resolve()
    except SpecError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    except OSError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    except Exception as e:  # noqa: BLE001 - report, never a traceback
        print(f"error: unexpected {type(e).__name__}: {e}", file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps({"output": str(out), "tracks": details}, indent=2))
    else:
        for line in lines:
            print(line)
        print(f"Wrote: {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
