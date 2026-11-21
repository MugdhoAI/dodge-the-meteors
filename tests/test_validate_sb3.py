"""Unit tests for tools.validate_sb3.

The tests build small .sb3 archives in temporary directories, so they run
without the real project file and without network access. Run them with:
    python3 -m unittest discover -s tests -v
"""

import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

import validate_sb3


def minimal_project():
    """A tiny valid project: one stage, one sprite, one script."""
    return {
        "targets": [
            {
                "isStage": True,
                "name": "Stage",
                "variables": {"var-score": ["score", "0"]},
                "lists": {},
                "broadcasts": {},
                "blocks": {
                    "hat1": {
                        "opcode": "event_whenflagclicked",
                        "next": "set1",
                        "parent": None,
                        "inputs": {},
                        "fields": {},
                        "shadow": False,
                        "topLevel": True,
                        "x": 0,
                        "y": 0,
                    },
                    "set1": {
                        "opcode": "data_setvariableto",
                        "next": None,
                        "parent": "hat1",
                        "inputs": {"VALUE": [1, [10, "0"]]},
                        "fields": {"VARIABLE": ["score", "var-score"]},
                        "shadow": False,
                        "topLevel": False,
                    },
                },
                "costumes": [
                    {
                        "name": "backdrop1",
                        "assetId": "aaabbbcc",
                        "md5ext": "aaabbbcc.svg",
                        "dataFormat": "svg",
                    }
                ],
                "sounds": [],
            },
            {
                "isStage": False,
                "name": "Sprite1",
                "variables": {},
                "lists": {},
                "broadcasts": {},
                "blocks": {},
                "costumes": [
                    {
                        "name": "costume1",
                        "assetId": "dddeeeff",
                        "md5ext": "dddeeeff.svg",
                        "dataFormat": "svg",
                    }
                ],
                "sounds": [],
            },
        ],
        "monitors": [
            {
                "id": "var-score",
                "mode": "default",
                "opcode": "data_variable",
                "params": {"VARIABLE": "score"},
                "spriteName": None,
                "value": "0",
                "width": 0,
                "height": 0,
                "x": 5,
                "y": 5,
                "visible": True,
            }
        ],
        "extensions": [],
        "meta": {"semver": "3.0.0", "vm": "15.1.1", "agent": "test"},
    }


class ValidatorTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def write_sb3(self, project, extra_files=None, omit=()):
        path = self.dir / "test.sb3"
        with zipfile.ZipFile(path, "w") as archive:
            archive.writestr("project.json", json.dumps(project))
            for name, data in (extra_files or {}).items():
                archive.writestr(name, data)
            if "aaabbbcc.svg" not in omit:
                archive.writestr("aaabbbcc.svg", "<svg/>")
            if "dddeeeff.svg" not in omit:
                archive.writestr("dddeeeff.svg", "<svg/>")
        return path

    def test_valid_project_passes(self):
        path = self.write_sb3(minimal_project())
        report = validate_sb3.validate_sb3(path)
        self.assertTrue(report.ok, report.errors)
        self.assertEqual(report.findings, [])

    def test_missing_costume_file_is_an_error(self):
        path = self.write_sb3(minimal_project(), omit=("aaabbbcc.svg",))
        report = validate_sb3.validate_sb3(path)
        self.assertFalse(report.ok)
        self.assertTrue(any("backdrop1" in e for e in report.errors),
                        report.errors)

    def test_dangling_next_reference_is_an_error(self):
        project = minimal_project()
        project["targets"][0]["blocks"]["set1"]["next"] = "no-such-block"
        path = self.write_sb3(project)
        report = validate_sb3.validate_sb3(path)
        self.assertFalse(report.ok)
        self.assertTrue(any("no-such-block" in e for e in report.errors),
                        report.errors)

    def test_unknown_variable_reference_is_an_error(self):
        project = minimal_project()
        project["targets"][0]["blocks"]["set1"]["fields"]["VARIABLE"] = \
            ["score", "no-such-variable"]
        path = self.write_sb3(project)
        report = validate_sb3.validate_sb3(path)
        self.assertFalse(report.ok)
        self.assertTrue(any("no-such-variable" in e for e in report.errors),
                        report.errors)

    def test_unused_variable_is_a_finding_not_an_error(self):
        project = minimal_project()
        project["targets"][0]["variables"]["var-unused"] = ["unused", 0]
        path = self.write_sb3(project)
        report = validate_sb3.validate_sb3(path)
        self.assertTrue(report.ok, report.errors)
        self.assertTrue(any("'unused'" in f for f in report.findings),
                        report.findings)

    def test_missing_project_json_is_an_error(self):
        path = self.dir / "empty.sb3"
        with zipfile.ZipFile(path, "w") as archive:
            archive.writestr("aaabbbcc.svg", "<svg/>")
        report = validate_sb3.validate_sb3(path)
        self.assertFalse(report.ok)
        self.assertTrue(any("project.json" in e for e in report.errors),
                        report.errors)

    def test_corrupt_archive_is_an_error(self):
        path = self.dir / "broken.sb3"
        path.write_bytes(b"this is not a zip file")
        report = validate_sb3.validate_sb3(path)
        self.assertFalse(report.ok)

    def test_real_project_file_is_structurally_valid(self):
        here = Path(__file__).resolve().parent.parent
        candidates = [here / "Dodge the Meteors - Mugdho.sb3",
                      here.parent / "Dodge the Meteors - Mugdho.sb3"]
        real = next((c for c in candidates if c.exists()), None)
        if real is None:
            self.skipTest("real project file is not checked out locally")
        report = validate_sb3.validate_sb3(real)
        self.assertTrue(report.ok, report.errors)
        self.assertTrue(any("'my variable'" in f for f in report.findings),
                        report.findings)


if __name__ == "__main__":
    unittest.main()
