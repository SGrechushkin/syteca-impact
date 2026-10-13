"""List the cases of an existing TestRail run (read-only).

Titles and folders come from the local index (data/index.jsonl), so run sync.py if cases are missing.
--compare shows how the run differs from the proposed list (runs/<NAME>.txt plus created cases from
runs/<NAME>.new.json) - i.e. what the user added/removed after the run was built.

Usage:
    py -X utf8 scripts/run_cases.py 42432
    py -X utf8 scripts/run_cases.py https://testrail.dev.local/index.php?/runs/view/42432 --ids-only
    py -X utf8 scripts/run_cases.py 42432 --compare runs/AC-61577.txt
"""
import argparse
import json
import re
from pathlib import Path

from tr_client import TestRail

INDEX = Path(__file__).resolve().parent.parent / "data" / "index.jsonl"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("run", help="run ID or URL")
    ap.add_argument("--ids-only", action="store_true", help="print only case IDs (for runs/<KEY>.txt)")
    ap.add_argument("--compare", metavar="CASES_FILE", help="diff the run against the proposed runs/<NAME>.txt")
    args = ap.parse_args()

    run_id = int(re.findall(r"\d+", args.run)[-1])
    tr = TestRail()
    run = tr.get(f"get_run/{run_id}")
    tests = tr.get_all(f"get_tests/{run_id}", "tests")
    case_ids = [t["case_id"] for t in tests]

    if args.ids_only:
        print(" ".join(f"C{i}" for i in case_ids))
        return

    index = {}
    with open(INDEX, encoding="utf-8") as f:
        for line in f:
            c = json.loads(line)
            index[c["id"]] = c

    def show(cid):
        c = index.get(cid)
        if c:
            print(f"C{cid} [{c['priority']}] ({c['updated_on']}) {c['path']}\n    {c['title']}")
        else:
            print(f"C{cid} (not in local index - run sync.py)")

    print(f"Run R{run_id} '{run['name']}': {len(case_ids)} cases")
    if args.compare:
        proposed = load_proposed(Path(args.compare))
        in_run = set(case_ids)
        added = [i for i in case_ids if i not in proposed]
        removed = [i for i in proposed if i not in in_run]
        print(f"Proposed: {len(proposed)}, kept: {len(in_run & set(proposed))}, "
              f"added by user: {len(added)}, removed by user: {len(removed)}")
        for title, ids in (("ADDED BY USER", added), ("REMOVED BY USER", removed)):
            print(f"\n--- {title} ({len(ids)}) ---")
            for cid in ids:
                show(cid)
        return
    if run.get("description"):
        print(f"Description: {run['description']}")
    for cid in case_ids:
        show(cid)


def load_proposed(cases_file):
    """Case IDs from runs/<NAME>.txt (comments skipped) plus created cases from runs/<NAME>.new.json."""
    text = "\n".join(l for l in cases_file.read_text("utf-8").splitlines() if not l.lstrip().startswith("#"))
    ids = [int(i) for i in re.findall(r"C?(\d+)", text)]
    drafts = cases_file.with_suffix(".new.json")
    if drafts.exists():
        ids += [c["id"] for c in json.loads(drafts.read_text("utf-8"))["cases"] if c.get("id")]
    return list(dict.fromkeys(ids))


if __name__ == "__main__":
    main()
