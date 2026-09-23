#!/usr/bin/env python3
"""Check the published KiCad library inventory and references."""

from pathlib import Path
import re
import sys


ROOT = Path(__file__).resolve().parent.parent
KICAD = ROOT / "kicad"
MODEL_PREFIX = "${TRUE_LIB}/kicad/TrueLib.3dshapes/"


def validate() -> None:
    symbols = (KICAD / "TrueLib.kicad_sym").read_text(encoding="utf-8-sig")
    names = re.findall(r'^\t\(symbol "([^"]+)"', symbols, re.MULTILINE)
    assert names and len(names) == len(set(names)), names
    links = re.findall(r'^\t\t\(property "Footprint" "([^"]*)"', symbols, re.MULTILINE)
    assert len(links) == len(names), links

    footprints = sorted((KICAD / "TrueLib.pretty").glob("*.kicad_mod"))
    models = sorted((KICAD / "TrueLib.3dshapes").glob("*.step"))
    assert footprints and models
    footprint_names = {path.stem for path in footprints}
    assert all(link.startswith("TrueLib:") and link[8:] in footprint_names for link in links if link)

    references = []
    for footprint in footprints:
        source = footprint.read_text(encoding="utf-8-sig")
        assert re.match(r'\(footprint "' + re.escape(footprint.stem) + r'"', source)
        links_in_file = re.findall(r'\(model "([^"]+)"', source)
        assert len(links_in_file) == 1, footprint
        reference = links_in_file[0]
        assert reference.startswith(MODEL_PREFIX), (footprint, reference)
        model = KICAD / "TrueLib.3dshapes" / reference[len(MODEL_PREFIX):]
        assert model.is_file(), model
        references.append(model.name)
        assert not re.search(r"(?<![A-Za-z])[A-Za-z]:[/\\]|/Users/|/home/|\$\{MY_LYB\}", source)
    assert len(set(references)) == len(footprints)
    assert set(references) == {path.name for path in models}
    assert not re.search(r"(?<![A-Za-z])[A-Za-z]:[/\\]|/Users/|/home/|\$\{MY_LYB\}|Library:", symbols)
    print(f"OK: {len(names)} symbols, {len(footprints)} footprints, {len(references)} STEP references")


if __name__ == "__main__":
    try:
        validate()
    except (AssertionError, OSError) as error:
        print(f"Validation failed: {error}", file=sys.stderr)
        raise SystemExit(1)
