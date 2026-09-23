#!/usr/bin/env python3
"""Register TrueLib in KiCad 10 user settings."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import platform
import re
import shutil
import sys
import tempfile
from datetime import datetime, timezone


NAME = "TrueLib"
VERSION = "10.0"
URIS = {
    "sym-lib-table": "${TRUE_LIB}/kicad/TrueLib.kicad_sym",
    "fp-lib-table": "${TRUE_LIB}/kicad/TrueLib.pretty",
}


def config_dir(system: str | None = None, home: Path | None = None,
               environ: dict[str, str] | None = None) -> Path:
    system = system or platform.system()
    home = home or Path.home()
    environ = environ if environ is not None else os.environ
    if environ.get("KICAD_CONFIG_HOME"):
        base = Path(environ["KICAD_CONFIG_HOME"])
    elif system == "Windows":
        if not environ.get("APPDATA"):
            raise ValueError("APPDATA is not set")
        base = Path(environ["APPDATA"]) / "kicad"
    elif system == "Darwin":
        base = home / "Library" / "Preferences" / "kicad"
    else:
        base = Path(environ.get("XDG_CONFIG_HOME", str(home / ".config"))) / "kicad"
    return base / VERSION


def quoted(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def table_entries(source: str, kind: str) -> list[tuple[int, int, str, str]]:
    if not re.match(r"\s*\(" + re.escape(kind) + r"(?:\s|\()", source):
        raise ValueError(f"Invalid {kind} root")
    entries = []
    depth = 0
    start = None
    in_string = False
    escaped = False
    comment = False
    for i, char in enumerate(source):
        if comment:
            if char == "\n":
                comment = False
            continue
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue
        if char == ";":
            comment = True
        elif char == '"':
            in_string = True
        elif char == "(":
            if depth == 1 and re.match(r"\(lib(?:\s|\()", source[i:]):
                start = i
            depth += 1
        elif char == ")":
            depth -= 1
            if depth < 0:
                raise ValueError(f"Unbalanced {kind}")
            if depth == 1 and start is not None:
                entry = source[start:i + 1]
                fields = {}
                for key in ("name", "uri"):
                    match = re.search(r"\(" + key + r'\s+("(?:\\.|[^"\\])*")', entry)
                    if not match:
                        raise ValueError(f"Missing {key} in {kind} entry")
                    fields[key] = json.loads(match.group(1))
                entries.append((start, i + 1, fields["name"], fields["uri"]))
                start = None
    if depth != 0 or in_string:
        raise ValueError(f"Unbalanced {kind}")
    return entries


def updated_table(source: str, kind: str, uri: str) -> str:
    entries = table_entries(source, kind)
    matches = [entry for entry in entries if entry[2] == NAME]
    if len(matches) > 1:
        raise ValueError(f"Duplicate {NAME} entries in {kind}")
    if matches:
        if matches[0][3] != uri:
            raise ValueError(f"{NAME} is already used by another library in {kind}: {matches[0][3]}")
        return source
    end = source.rfind(")")
    if end < 0:
        raise ValueError(f"Invalid {kind}")
    entry = (f'\t(lib (name "{NAME}") (type "KiCad") '
             f'(uri {quoted(uri)}) (options "") (descr "KiCad and FreeCAD shared library"))\n')
    return source[:end] + entry + source[end:]


def write_atomic(path: Path, content: bytes) -> None:
    fd, name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(content)
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def run(repo: Path, settings: Path, check: bool) -> int:
    required = [repo / "kicad" / "TrueLib.kicad_sym", repo / "kicad" / "TrueLib.pretty"]
    if any(not path.exists() for path in required):
        raise ValueError("Run this script from a complete TrueLib clone")
    paths = [settings / "kicad_common.json", *[settings / name for name in URIS]]
    missing = [str(path) for path in paths if not path.is_file()]
    if missing:
        raise ValueError("Open KiCad 10 once to create its global settings and tables: " + ", ".join(missing))
    external = os.environ.get("TRUE_LIB")
    if external and Path(external).resolve() != repo:
        raise ValueError("External TRUE_LIB overrides KiCad settings; remove or update it first")

    original = {path: path.read_bytes() for path in paths}
    common = json.loads(original[paths[0]].decode("utf-8-sig"))
    variables = common.setdefault("environment", {}).setdefault("vars", {})
    if not isinstance(variables, dict):
        raise ValueError("Invalid KiCad path variables")
    target = repo.as_posix()
    variable_changed = variables.get("TRUE_LIB") != target
    changed = variable_changed
    variables["TRUE_LIB"] = target
    planned = {paths[0]: ((json.dumps(common, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
                          if variable_changed else original[paths[0]])}
    for path, (name, uri) in zip(paths[1:], URIS.items()):
        source = original[path].decode("utf-8-sig")
        result = updated_table(source, name.replace("-", "_"), uri)
        planned[path] = result.encode("utf-8") if result != source else original[path]
        changed |= result != source

    if check:
        print("TrueLib is configured" if not changed else "TrueLib needs setup or path update")
        return 0 if not changed else 1
    changes = [path for path in paths if planned[path] != original[path]]
    if not changes:
        print("TrueLib is already configured")
        return 0
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backups = {}
    try:
        for path in changes:
            backup = path.with_name(f"{path.name}.bak.{stamp}")
            index = 1
            while backup.exists():
                backup = path.with_name(f"{path.name}.bak.{stamp}.{index}")
                index += 1
            shutil.copy2(path, backup)
            backups[path] = backup
        for path in changes:
            write_atomic(path, planned[path])
    except Exception:
        for path, backup in backups.items():
            shutil.copy2(backup, path)
        raise
    print(f"TrueLib configured for KiCad 10: {target}")
    print(f"Backups: {settings}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Check without changing files")
    parser.add_argument("--config-dir", type=Path, help="KiCad 10 settings directory (for testing)")
    args = parser.parse_args()
    repo = Path(__file__).resolve().parent.parent
    try:
        return run(repo, args.config_dir or config_dir(), args.check)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
