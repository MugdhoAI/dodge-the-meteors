#!/usr/bin/env python3
"""Validate the Dodge the Meteors Scratch project file.

Checks the .sb3 archive: it must be a valid zip, project.json must parse,
every costume and sound file must be present in the archive, and every block
reference (variable, custom block, parent, next, substack, condition) must
resolve. Gameplay notes such as unused variables and unused sounds are
reported as findings, not errors, so a structurally sound project passes.

Usage:
    python3 tools/validate_sb3.py [--sb3 PATH]

The default path is the project file next to this tools directory, or the
file in the current directory when run from the repository root. Exit code
0 means the project is structurally valid.
"""

import argparse
import json
import sys
import zipfile
from pathlib import Path


class Report:
    """Collects errors and findings while a project is checked."""

    def __init__(self):
        self.errors = []
        self.findings = []

    def error(self, message):
        self.errors.append(message)

    def finding(self, message):
        self.findings.append(message)

    @property
    def ok(self):
        return not self.errors


def _menu_triples(value, out):
    """Collect [12, name, id] triples found anywhere inside a JSON value."""
    if isinstance(value, list):
        if len(value) == 3 and value[0] == 12 and isinstance(value[1], str) \
                and isinstance(value[2], str):
            out.append((value[1], value[2]))
        for item in value:
            _menu_triples(item, out)
    elif isinstance(value, dict):
        for item in value.values():
            _menu_triples(item, out)


def _block_inputs_references(block, block_ids, report, where):
    """Check the block ids referenced by one block's inputs."""
    for name, entry in (block.get("inputs") or {}).items():
        if not isinstance(entry, list) or len(entry) < 2:
            report.error(f"{where}: block {block['opcode']} has a bad "
                         f"input {name!r}: {entry!r}")
            continue
        kind, value = entry[0], entry[1]
        if kind == 2 and isinstance(value, str):
            if value not in block_ids:
                report.error(f"{where}: block {block['opcode']} input "
                             f"{name!r} points at missing block {value!r}")
        elif kind == 3 and isinstance(value, str):
            if value not in block_ids:
                report.error(f"{where}: block {block['opcode']} input "
                             f"{name!r} points at missing block {value!r}")


def validate_project(project, archive_names, report):
    """Check one parsed project.json against the archive file list."""
    targets = project.get("targets")
    if not isinstance(targets, list) or not targets:
        report.error("project has no targets")
        return
    stages = [t for t in targets if t.get("isStage")]
    if len(stages) != 1:
        report.error(f"project has {len(stages)} stages, expected exactly 1")

    variables = {}
    for target in targets:
        for var_id, var in (target.get("variables") or {}).items():
            variables[var_id] = (target["name"], var[0])

    sound_ids = set()
    costume_ids = set()
    for target in targets:
        for sound in target.get("sounds") or []:
            sound_ids.add(sound.get("assetId"))
            if sound.get("md5ext") not in archive_names:
                report.error(f"{target['name']}: sound {sound.get('name')!r} "
                             f"file {sound.get('md5ext')!r} is missing "
                             f"from the archive")
        for costume in target.get("costumes") or []:
            costume_ids.add(costume.get("assetId"))
            if costume.get("md5ext") not in archive_names:
                report.error(f"{target['name']}: costume "
                             f"{costume.get('name')!r} file "
                             f"{costume.get('md5ext')!r} is missing "
                             f"from the archive")

    known_ids = set(variables) | sound_ids | costume_ids
    used_variables = set()
    used_sounds = set()
    for target in targets:
        blocks = target.get("blocks") or {}
        block_ids = set(blocks)
        prototypes = {}
        for block_id, block in blocks.items():
            where = f"{target['name']} block {block_id}"
            if block.get("parent") is None and not block.get("topLevel"):
                report.error(f"{where}: block {block['opcode']} has no "
                             f"parent but is not top level")
            if block.get("parent") is not None \
                    and block["parent"] not in block_ids:
                report.error(f"{where}: block {block['opcode']} points at "
                             f"missing parent {block['parent']!r}")
            if block.get("next") is not None \
                    and block["next"] not in block_ids:
                report.error(f"{where}: block {block['opcode']} points at "
                             f"missing next block {block['next']!r}")
            _block_inputs_references(block, block_ids, report, where)
            for field_name, field in (block.get("fields") or {}).items():
                if field_name == "VARIABLE" and isinstance(field, list) \
                        and len(field) == 2:
                    used_variables.add(field[1])
                    if field[1] not in variables:
                        report.error(f"{where}: field VARIABLE points at "
                                     f"unknown variable {field[1]!r}")
            triples = []
            _menu_triples(block.get("inputs"), triples)
            for name, ref_id in triples:
                if ref_id in variables:
                    used_variables.add(ref_id)
                elif ref_id in sound_ids:
                    used_sounds.add(ref_id)
                elif ref_id in costume_ids:
                    pass
                else:
                    report.error(f"{where}: block {block['opcode']} "
                                 f"references unknown id {ref_id!r} "
                                 f"({name!r})")
            if block.get("opcode") == "procedures_prototype":
                mutation = block.get("mutation") or {}
                prototypes[mutation.get("proccode")] = mutation
            if block.get("opcode") == "procedures_call":
                mutation = block.get("mutation") or {}
                proccode = mutation.get("proccode")
                if proccode not in prototypes:
                    report.error(f"{where}: custom block call {proccode!r} "
                                 f"has no matching definition in "
                                 f"{target['name']}")
                else:
                    try:
                        arg_ids = json.loads(
                            prototypes[proccode].get("argumentids", "[]"))
                    except json.JSONDecodeError:
                        arg_ids = []
                    for arg_id in block.get("inputs") or {}:
                        if arg_id not in arg_ids:
                            report.error(f"{where}: custom block call passes "
                                         f"unknown argument {arg_id!r}")

    for var_id, (target_name, var_name) in variables.items():
        if var_id not in used_variables:
            report.finding(f"variable {var_name!r} in {target_name} is "
                           f"declared but never used by any block")
    for target in targets:
        for sound in target.get("sounds") or []:
            if sound.get("assetId") not in used_sounds:
                report.finding(f"sound {sound.get('name')!r} in "
                               f"{target['name']} is never played by any "
                               f"block")

    for monitor in project.get("monitors") or []:
        var_id = monitor.get("id")
        if var_id not in variables:
            report.error(f"monitor {monitor.get('id')!r} points at unknown "
                         f"variable")
        elif monitor.get("params", {}).get("VARIABLE") != variables[var_id][1]:
            report.error(f"monitor for variable {var_id!r} names "
                         f"{monitor['params'].get('VARIABLE')!r} but the "
                         f"variable is called "
                         f"{variables[var_id][1]!r}")


def validate_sb3(path):
    """Validate one .sb3 file and return its report."""
    report = Report()
    try:
        archive = zipfile.ZipFile(path)
    except (zipfile.BadZipFile, OSError) as exc:
        report.error(f"cannot open {path}: {exc}")
        return report
    with archive:
        names = set(archive.namelist())
        bad = archive.testzip()
        if bad is not None:
            report.error(f"archive entry {bad!r} is corrupt")
        if "project.json" not in names:
            report.error("archive has no project.json")
            return report
        try:
            project = json.loads(archive.read("project.json"))
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            report.error(f"project.json does not parse: {exc}")
            return report
        validate_project(project, names, report)
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sb3", type=Path, default=None,
                        help="path to the .sb3 file")
    args = parser.parse_args(argv)
    path = args.sb3
    if path is None:
        here = Path(__file__).resolve().parent.parent
        candidates = [here / "Dodge the Meteors - Mugdho.sb3",
                      Path.cwd() / "Dodge the Meteors - Mugdho.sb3"]
        path = next((c for c in candidates if c.exists()), candidates[0])
    report = validate_sb3(path)
    print(f"Checked {path}")
    if report.errors:
        print(f"Errors ({len(report.errors)}):")
        for message in report.errors:
            print(f"  - {message}")
    else:
        print("No structural errors.")
    if report.findings:
        print(f"Findings ({len(report.findings)}):")
        for message in report.findings:
            print(f"  - {message}")
    return 0 if report.ok else 1


if __name__ == "__main__":
    sys.exit(main())
