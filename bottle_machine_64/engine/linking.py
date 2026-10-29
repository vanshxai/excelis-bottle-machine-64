"""
Drive links: which part turns / moves which. Suggestions come from part types; the user confirms.
active  = driven directly by a motor
passive = driven by an active (or another passive) part
"""
from part_types import is_motor, TYPES

# (child type, parent type) -> how the load travels from the child up to the parent
COUPLINGS = {
    ("shaft", "motor"): "direct_torque",
    ("drive_pulley", "motor"): "direct_torque",
    ("rotary_disk", "shaft"): "direct_torque",
    ("belt", "drive_pulley"): "force_to_torque_parent",
    ("idler_pulley", "belt"): "torque_to_force_child",
    ("flipper_arm", "belt"): "force_direct",
}
PARENT_TYPES = {}
for (c, p), _ in COUPLINGS.items():
    PARENT_TYPES.setdefault(c, []).append(p)


def _tkey(t):
    return "motor" if is_motor(t) else t


def coupling(child_type, parent_type):
    return COUPLINGS.get((_tkey(child_type), _tkey(parent_type)))


def suggest_parents(parts):
    """parts: {pn: {'type','section'}} -> {pn: (parent_pn or None, reason)}"""
    out = {}
    for pn, p in parts.items():
        wanted = PARENT_TYPES.get(_tkey(p["type"]))
        if not wanted:
            continue
        same = [q for q, d in parts.items() if q != pn and _tkey(d["type"]) in wanted and d["section"] == p["section"]]
        anywhere = [q for q, d in parts.items() if q != pn and _tkey(d["type"]) in wanted]
        pick = same if len(same) == 1 else (anywhere if len(anywhere) == 1 else None)
        if pick:
            out[pn] = (pick[0], "the only " + "/".join(wanted) + (" in its section" if pick is same else " in the machine"))
        else:
            out[pn] = (None, "more than one candidate - you choose" if (same or anywhere) else "no candidate parent found")
    return out


def validate_links(parts, links):
    """links: {child_pn: parent_pn}. Returns list of problems (empty = ok)."""
    problems = []
    for pn, p in parts.items():
        t = p["type"]
        if TYPES[t]["kind"] in ("static", "motor"):
            if pn in links:
                problems.append(f"{pn} is a {TYPES[t]['label']} and cannot be driven by another part.")
            continue
        if pn not in links or not links[pn]:
            problems.append(f"{pn} ({TYPES[t]['label']}) has no driving part set.")
            continue
        par = links[pn]
        if par not in parts:
            problems.append(f"{pn}: driving part '{par}' is not in the machine.")
            continue
        if coupling(t, parts[par]["type"]) is None:
            problems.append(f"{pn} ({TYPES[t]['label']}) driven by {par} ({TYPES[parts[par]['type']]['label']}): "
                            "this combination is not supported yet.")
    # every driven part must reach a motor without a loop
    for pn in parts:
        seen, cur = set(), pn
        while cur in links and links[cur]:
            if cur in seen:
                problems.append(f"{pn}: the drive links form a loop.")
                break
            seen.add(cur)
            cur = links[cur]
        else:
            if TYPES[parts[pn]["type"]]["kind"] == "driven" and not is_motor(parts[cur]["type"]):
                problems.append(f"{pn}: following its drive links does not end at a motor.")
    return problems


def chain_to_motor(pn, links):
    chain = [pn]
    while chain[-1] in links and links[chain[-1]]:
        chain.append(links[chain[-1]])
    return chain


def role_of(pn, parts, links):
    t = parts[pn]["type"]
    if is_motor(t):
        return "source"
    if TYPES[t]["kind"] == "static":
        return "static"
    return "active" if is_motor(parts[links[pn]]["type"]) else "passive"
