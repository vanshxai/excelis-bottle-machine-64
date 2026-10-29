"""
Match STEP part names to BOM rows. Exact matches only; the one tolerated variation is the
instance suffix CAD programs append ("MS00201-1", "MS00201<1>", "MS00201:1", "MS00201_1").
A stripped name is accepted only if it equals a BOM part number exactly. No fuzzy matching.
"""
import re

_SUFFIXES = [r"<\d+>$", r":\d+(_[0-9a-f]{4,})?$", r"-\d+$", r"_\d+$"]


def _candidates(name):
    yield name, "exact"
    for pat in _SUFFIXES:
        stripped = re.sub(pat, "", name)
        if stripped != name:
            yield stripped, "instance-suffix removed"


def match(geometry_parts, bom_rows):
    by_pn = {r["part_number"]: r for r in bom_rows}
    by_desc = {}
    for r in bom_rows:
        by_desc.setdefault(r["description"].strip().lower(), []).append(r)

    matched, unmatched_step = [], []
    for p in geometry_parts:
        hit = None
        for cand, kind in _candidates(p["name"]):
            if cand in by_pn:
                hit = (by_pn[cand], kind)
                break
        if not hit:
            rows = by_desc.get(p["name"].strip().lower(), [])
            if len(rows) == 1:
                hit = (rows[0], "matched on description")
        if hit and not hit[0]["is_assembly"]:
            matched.append({"step_id": p["id"], "step_name": p["name"], "path": p["path"],
                            "part_number": hit[0]["part_number"], "how": hit[1]})
        else:
            unmatched_step.append({"step_id": p["id"], "step_name": p["name"], "path": p["path"]})

    counts = {}
    for m in matched:
        counts[m["part_number"]] = counts.get(m["part_number"], 0) + 1
    leaf_rows = [r for r in bom_rows if not r["is_assembly"]]
    bom_not_in_step = [r["part_number"] for r in leaf_rows if r["part_number"] not in counts]
    qty_mismatch = [{"part_number": r["part_number"], "bom_qty": r["qty"], "step_count": counts[r["part_number"]]}
                    for r in leaf_rows if r["part_number"] in counts and counts[r["part_number"]] != r["qty"]]

    # which assembly rows appear as nodes in the STEP tree
    path_nodes = {n for p in geometry_parts for n in p["path"]}
    asm_rows = {r["part_number"]: r for r in bom_rows if r["is_assembly"]}
    assemblies = [{"part_number": pn, "description": r["description"], "in_step": pn in path_nodes}
                  for pn, r in asm_rows.items()]

    problems = []
    for u in unmatched_step:
        problems.append(f"STEP part '{u['step_name']}' has no matching BOM row.")
    for pn in bom_not_in_step:
        problems.append(f"BOM part '{pn}' was not found in the STEP file.")
    for q in qty_mismatch:
        problems.append(f"{q['part_number']}: BOM says {q['bom_qty']} but the STEP file has {q['step_count']}.")
    return {"matched": matched, "unmatched_step": unmatched_step, "bom_not_in_step": bom_not_in_step,
            "qty_mismatch": qty_mismatch, "assemblies": assemblies, "problems": problems,
            "ok": not problems}
