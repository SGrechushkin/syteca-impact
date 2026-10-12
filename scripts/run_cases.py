"""List the cases of an existing TestRail run (read-only).

Titles and folders come from the local index (data/index.jsonl), so run sync.py if cases are missing.

Usage:
    py -X utf8 scripts/run_cases.py 42432
    py -X utf8 scripts/run_cases.py https://testrail.dev.local/index.php?/runs/view/42432 --ids-only
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

    print(f"Run R{run_id} '{run['name']}': {len(case_ids)} cases")
    if run.get("description"):
        print(f"Description: {run['description']}")
    for cid in case_ids:
        c = index.get(cid)
        if c:
            print(f"C{cid} [{c['priority']}] {c['path']}\n    {c['title']}")
        else:
            print(f"C{cid} (not in local index - run sync.py)")


if __name__ == "__main__":
    main()
