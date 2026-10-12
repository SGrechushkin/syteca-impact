"""Print full details of cases from the local index (data/index.jsonl).

Usage:
    py -X utf8 scripts/show.py C251603883 C241097080
    py -X utf8 scripts/show.py 251603883 --max 3000
"""
import argparse
import json
from pathlib import Path

INDEX = Path(__file__).resolve().parent.parent / "data" / "index.jsonl"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ids", nargs="+", help="case IDs (C123 or 123)")
    ap.add_argument("--max", type=int, default=1500, help="max characters per field")
    args = ap.parse_args()

    wanted = [int(i.upper().lstrip("C")) for i in args.ids]
    found = {}
    with open(INDEX, encoding="utf-8") as f:
        for line in f:
            c = json.loads(line)
            if c["id"] in wanted:
                found[c["id"]] = c

    for cid in wanted:
        c = found.get(cid)
        if not c:
            print(f"===== C{cid}: not in index (run sync.py?)\n")
            continue
        print(f"===== C{cid} [{c['priority']}] ({c['updated_on']}) {c['path']}\n{c['title']}")
        if c.get("refs"):
            print(f"REFS: {c['refs']}")
        for k in ("preconditions", "steps", "expected"):
            if c[k]:
                print(f"{k.upper()}:\n{c[k][:args.max]}")
        print()


if __name__ == "__main__":
    main()
