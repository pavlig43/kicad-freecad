import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from scripts.install import config_dir, run, URIS


ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / "codexwork"


class InstallTests(unittest.TestCase):
    def setUp(self):
        WORK.mkdir(exist_ok=True)
        self.tmp = tempfile.TemporaryDirectory(dir=WORK)
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.repo = self.base / "clone one"
        self.repo2 = self.base / "clone two"
        for repo in (self.repo, self.repo2):
            (repo / "kicad" / "TrueLib.pretty").mkdir(parents=True)
            (repo / "kicad" / "TrueLib.kicad_sym").write_text("symbol", encoding="utf-8")
        self.settings = self.base / "settings"
        self.settings.mkdir()
        (self.settings / "kicad_common.json").write_text(
            json.dumps({"environment": {"vars": {"OTHER": "keep"}}, "unrelated": 42}), encoding="utf-8")
        (self.settings / "sym-lib-table").write_text(
            '(sym_lib_table\n\t(lib (name "Other") (type "KiCad") (uri "/other.sym") (options "") (descr ""))\n)\n',
            encoding="utf-8")
        (self.settings / "fp-lib-table").write_text(
            '(fp_lib_table\n\t(lib (name "Other") (type "KiCad") (uri "/other.pretty") (options "") (descr ""))\n)\n',
            encoding="utf-8")

    def snapshot(self):
        return {name: (self.settings / name).read_bytes()
                for name in ("kicad_common.json", *URIS)}

    def test_first_repeat_move_and_check(self):
        with patch.dict(os.environ, {"TRUE_LIB": ""}):
            before = self.snapshot()
            self.assertEqual(run(self.repo, self.settings, True), 1)
            self.assertEqual(self.snapshot(), before)
            self.assertEqual(run(self.repo, self.settings, False), 0)
            installed = self.snapshot()
            self.assertEqual(run(self.repo, self.settings, True), 0)
            self.assertEqual(run(self.repo, self.settings, False), 0)
            self.assertEqual(self.snapshot(), installed)
            self.assertEqual(run(self.repo2, self.settings, False), 0)
            moved = self.snapshot()
            self.assertNotEqual(moved["kicad_common.json"], installed["kicad_common.json"])
            self.assertEqual(moved["sym-lib-table"], installed["sym-lib-table"])
            self.assertEqual(moved["fp-lib-table"], installed["fp-lib-table"])
            vars = json.loads(moved["kicad_common.json"])["environment"]["vars"]
            self.assertEqual(vars["TRUE_LIB"], self.repo2.as_posix())
            self.assertEqual(vars["OTHER"], "keep")
            self.assertEqual(len(list(self.settings.glob("*.bak.*"))), 4)

    def test_occupied_name_changes_nothing(self):
        table = self.settings / "fp-lib-table"
        source = table.read_text(encoding="utf-8")
        table.write_text(source.replace("\n)\n", '\t(lib (name "TrueLib") (type "KiCad") (uri "/foreign.pretty") (options "") (descr ""))\n)\n'), encoding="utf-8")
        before = self.snapshot()
        with patch.dict(os.environ, {"TRUE_LIB": ""}):
            with self.assertRaisesRegex(ValueError, "already used"):
                run(self.repo, self.settings, False)
        self.assertEqual(self.snapshot(), before)
        self.assertEqual(list(self.settings.glob("*.bak.*")), [])

    def test_os_settings_paths(self):
        home = self.base / "home"
        appdata = self.base / "AppData" / "Roaming"
        self.assertEqual(config_dir("Windows", home, {"APPDATA": str(appdata)}),
                         appdata / "kicad/10.0")
        self.assertEqual(config_dir("Linux", home, {}), home / ".config/kicad/10.0")
        self.assertEqual(config_dir("Darwin", home, {}), home / "Library/Preferences/kicad/10.0")
        custom = self.base / "custom" / "kicad"
        self.assertEqual(config_dir("Linux", home, {"KICAD_CONFIG_HOME": str(custom)}),
                         custom / "10.0")


if __name__ == "__main__":
    unittest.main()
