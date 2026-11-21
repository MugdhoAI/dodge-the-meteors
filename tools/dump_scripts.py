#!/usr/bin/env python3
"""Print the scripts of the Dodge the Meteors Scratch project as text.

Reading a .sb3 file needs the Scratch editor, so this tool dumps each
sprite's scripts in a readable form for review in a terminal or a pull
request. It reads project.json out of the archive and walks each top level
script, indenting blocks that sit inside a loop or a condition.

Usage:
    python3 tools/dump_scripts.py [--sb3 PATH]
"""

import argparse
import json
import sys
import zipfile
from pathlib import Path

# Blocks whose inputs hold a nested stack of blocks.
STACK_INPUTS = ("SUBSTACK", "SUBSTACK2")


def _value(entry, blocks, variables):
    """Render one block input entry as short text."""
    if not isinstance(entry, list) or len(entry) < 2:
        return repr(entry)
    kind, value = entry[0], entry[1]
    if kind == 1 and isinstance(value, str) and value in blocks:
        return _block_text(value, blocks, variables, nested=True)
    if kind == 1 and isinstance(value, list):
        if len(value) == 3 and value[0] == 12:
            return variables.get(value[2], value[1])
        if len(value) == 2:
            return repr(value[1])
        return repr(value)
    if kind in (2, 3) and isinstance(value, str):
        return _block_text(value, blocks, variables, nested=True)
    if kind == 3 and isinstance(value, list):
        return _value([1, value], blocks, variables)
    return repr(value)


def _block_text(block_id, blocks, variables, nested=False):
    """Render one block and, unless nested, the blocks chained after it."""
    block = blocks[block_id]
    parts = [block["opcode"]]
    for name, field in (block.get("fields") or {}).items():
        parts.append(f"{name}={field[0]!r}")
    for name, entry in (block.get("inputs") or {}).items():
        if name in STACK_INPUTS:
            continue
        parts.append(f"{name}={_value(entry, blocks, variables)}")
    text = " ".join(parts)
    if nested:
        return f"[{text}]"
    return text


def _walk(block_id, blocks, variables, indent, lines):
    """Append one chain of blocks, recursing into nested stacks."""
    current = block_id
    while current is not None:
        block = blocks[current]
        lines.append("  " * indent + _block_text(current, blocks, variables))
        for name in STACK_INPUTS:
            entry = (block.get("inputs") or {}).get(name)
            if isinstance(entry, list) and len(entry) == 2 \
                    and isinstance(entry[1], str):
                lines.append("  " * indent + f"{name}:")
                _walk(entry[1], blocks, variables, indent + 1, lines)
        current = block.get("next")


def _label_arguments(project):
    """Rename custom block call inputs from argument ids to argument names.

    A procedures_call stores its arguments under opaque ids. The matching
    procedures_prototype in the same sprite maps those ids to the names
    the author chose, so the dump shows "speed=Speed" instead of an id.
    """
    import copy

    project = copy.deepcopy(project)
    for target in project.get("targets", []):
        blocks = target.get("blocks") or {}
        prototypes = {}
        for block in blocks.values():
            if block.get("opcode") != "procedures_prototype":
                continue
            mutation = block.get("mutation") or {}
            try:
                ids = json.loads(mutation.get("argumentids", "[]"))
                names = json.loads(mutation.get("argumentnames", "[]"))
            except json.JSONDecodeError:
                continue
            prototypes[mutation.get("proccode")] = dict(zip(ids, names))
        for block in blocks.values():
            if block.get("opcode") != "procedures_call":
                continue
            mutation = block.get("mutation") or {}
            mapping = prototypes.get(mutation.get("proccode"), {})
            inputs = block.get("inputs") or {}
            block["inputs"] = {mapping.get(k, k): v for k, v in inputs.items()}
    return project


def dump_scripts(project):
    """Return the readable script listing for one parsed project.json."""
    project = _label_arguments(project)
    variables = {}
    for target in project.get("targets", []):
        for var_id, var in (target.get("variables") or {}).items():
            variables[var_id] = var[0]
    lines = []
    for target in project.get("targets", []):
        lines.append(f"== {target['name']} ==")
        blocks = target.get("blocks") or {}
        tops = [b for b in blocks.values() if b.get("topLevel")]
        if not tops:
            lines.append("  (no scripts)")
        for block in tops:
            block_id = next(k for k, v in blocks.items() if v is block)
            _walk(block_id, blocks, variables, 1, lines)
        lines.append("")
    return "\n".join(lines)


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
    try:
        with zipfile.ZipFile(path) as archive:
            project = json.loads(archive.read("project.json"))
    except (zipfile.BadZipFile, OSError, json.JSONDecodeError) as exc:
        print(f"cannot read {path}: {exc}", file=sys.stderr)
        return 1
    print(dump_scripts(project))
    return 0


if __name__ == "__main__":
    sys.exit(main())
