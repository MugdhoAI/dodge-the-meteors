"""Unit tests for tools.dump_scripts.

Run them with:
    python3 -m unittest discover -s tests -v
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

import dump_scripts
from test_validate_sb3 import minimal_project


class DumpScriptsTestCase(unittest.TestCase):
    def test_lists_each_sprite(self):
        out = dump_scripts.dump_scripts(minimal_project())
        self.assertIn("== Stage ==", out)
        self.assertIn("== Sprite1 ==", out)
        self.assertIn("(no scripts)", out)

    def test_lists_blocks_in_order(self):
        out = dump_scripts.dump_scripts(minimal_project())
        self.assertIn("event_whenflagclicked", out)
        self.assertIn("data_setvariableto VARIABLE='score' VALUE='0'", out)
        self.assertLess(out.index("event_whenflagclicked"),
                        out.index("data_setvariableto"))

    def test_renders_variable_names_not_ids(self):
        out = dump_scripts.dump_scripts(minimal_project())
        self.assertNotIn("var-score", out)
        self.assertIn("score", out)

    def test_custom_block_argument_uses_its_name(self):
        project = minimal_project()
        sprite = project["targets"][1]
        sprite["blocks"] = {
            "hat": {
                "opcode": "event_whenflagclicked", "next": "call",
                "parent": None, "inputs": {}, "fields": {},
                "shadow": False, "topLevel": True, "x": 0, "y": 0,
            },
            "call": {
                "opcode": "procedures_call", "next": None, "parent": "hat",
                "inputs": {"arg-id": [1, [10, "3"]]},
                "fields": {}, "shadow": False, "topLevel": False,
                "mutation": {"tagName": "mutation", "children": [],
                             "proccode": "Do thing %s",
                             "argumentids": '["arg-id"]', "warp": "false"},
            },
            "def": {
                "opcode": "procedures_definition", "next": "proto",
                "parent": None, "inputs": {"custom_block": [2, "proto"]},
                "fields": {}, "shadow": False, "topLevel": True,
                "x": 0, "y": 0,
            },
            "proto": {
                "opcode": "procedures_prototype", "next": None,
                "parent": "def", "inputs": {}, "fields": {},
                "shadow": False, "topLevel": False,
                "mutation": {"tagName": "mutation", "children": [],
                             "proccode": "Do thing %s",
                             "argumentids": '["arg-id"]',
                             "argumentnames": '["steps"]',
                             "argumentdefaults": '[""]', "warp": "false"},
            },
        }
        out = dump_scripts.dump_scripts(project)
        self.assertIn("procedures_call steps='3'", out)
        self.assertNotIn("arg-id", out)

    def test_real_project_dump_names_the_sprites_and_scripts(self):
        here = Path(__file__).resolve().parent.parent
        candidates = [here / "Dodge the Meteors - Mugdho.sb3",
                      here.parent / "Dodge the Meteors - Mugdho.sb3"]
        real = next((c for c in candidates if c.exists()), None)
        if real is None:
            self.skipTest("real project file is not checked out locally")
        import json
        import zipfile
        with zipfile.ZipFile(real) as archive:
            project = json.loads(archive.read("project.json"))
        out = dump_scripts.dump_scripts(project)
        for name in ("Stage", "Rocketship", "Meteor"):
            self.assertIn(f"== {name} ==", out)
        self.assertIn("KEY_OPTION='left arrow'", out)
        self.assertIn("BACKDROP='Game Over'", out)


if __name__ == "__main__":
    unittest.main()
