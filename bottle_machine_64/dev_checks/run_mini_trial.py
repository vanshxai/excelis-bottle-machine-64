"""Internal: run the whole mini-sorter pipeline from the command line (same engine the app uses)."""
import json, os, sys
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, os.path.join(ROOT, "engine"))
import builder, linking
from part_types import TYPES

def main():
    D = os.path.join(ROOT, "testdata", "mini_sorter")
    an = builder.analyze(os.path.join(D, "mini_sorter.step"), os.path.join(D, "mini_sorter_bom.csv"))
    print("STEP parts:", an["geometry"]["part_count"], "| BOM rows:", len(an["bom"]["rows"]), "| match ok:", an["match"]["ok"], an["match"]["problems"])
    types = {pn: p["suggested_type"] for pn, p in an["parts"].items()}
    print("suggested types:", types)
    typed = {pn: {"type": t, "section": an["parts"][pn]["section"]} for pn, t in types.items()}
    sug = linking.suggest_parents(typed)
    links = {pn: par for pn, (par, why) in sug.items() if par}
    print("suggested links:", links)
    answers = json.load(open(os.path.join(D, "test_answers.json")))
    answers["types"], answers["links"] = types, links
    print("validate:", builder.validate(an, answers) or "no problems")
    out = os.path.join(ROOT, "projects", "mini_sorter")
    s = builder.build(an, answers, out, os.path.join(D, "mini_sorter.step"), os.path.join(D, "mini_sorter_bom.csv"), progress=print)
    print(json.dumps({k: v for k, v in s.items() if k != "tree"}, indent=1))
    sig = json.load(open(os.path.join(out, "signatures.json")))
    print("\nmotor slopes:", {m: round(v["Kt"], 3) for m, v in sig["motors"].items()}, "N*m per A")
    for pn, r in sig["parts"].items():
        L = r["levels"]
        print(f"{pn} on {r['motor']}: dI at ok/warn/crit = {L['ok_max']['delta_current_A']:.4f} / {L['warning']['delta_current_A']:.4f} / {L['critical']['delta_current_A']:.4f} A  -> detectable: {r['detectable_at_critical']}")


if __name__ == "__main__":
    main()
