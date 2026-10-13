"""Search the local case index (data/index.jsonl).

Each argument is a term group; a case matches when EVERY group matches.
Inside a group, alternatives are separated by "|" (regex, case-insensitive).
Obsolete folders (DEPRECATED, NOT IMPLEMENTED YET, to delete, To remove, PEDM / DEL) are skipped unless --all.
DRAFT folders are searched (possibly not reviewed yet).

Usage:
    py -X utf8 scripts/search.py "secret" "permission|PAM User"
    py -X utf8 scripts/search.py --path "PAM" "just in time|JIT" --full
    py -X utf8 scripts/search.py "ini" "upload" --title-only --by-section   # counts per folder first
"""
import argparse
import json
import re
from collections import Counter
from pathlib import Path

INDEX = Path(__file__).resolve().parent.parent / "data" / "index.jsonl"
OBSOLETE = re.compile(r"DEPRECATED|DELETED|NOT IMPLEMENTED YET|to delete|To remove|\[TBD\]|(^|/ )DEL( /|$)", re.I)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("terms", nargs="*")
    ap.add_argument("--path", help="regex the section path must match")
    ap.add_argument("--title-only", action="store_true", help="match terms against title only")
    ap.add_argument("--all", action="store_true", help="include obsolete folders")
    ap.add_argument("--full", action="store_true", help="print preconditions/steps/expected")
    ap.add_argument("--limit", type=int, default=0, help="max cases to print (default: all)")
    ap.add_argument("--by-section", action="store_true",
                    help="print only match counts per section (narrow down with --path afterwards)")
    args = ap.parse_args()

    groups = [re.compile(t, re.I) for t in args.terms]
    path_re = re.compile(args.path, re.I) if args.path else None
    hits = []
    with open(INDEX, encoding="utf-8") as f:
        for line in f:
            c = json.loads(line)
            if not args.all and OBSOLETE.search(c["path"]):
                continue
            if path_re and not path_re.search(c["path"]):
                continue
            text = c["title"] if args.title_only else " ".join(
                str(c[k] or "") for k in ("title", "path", "preconditions", "steps", "expected"))
            if all(g.search(text) for g in groups):
                hits.append(c)

    if args.by_section:
        for path, n in Counter(c["path"] for c in hits).most_common():
            print(f"{n:5}  {path}")
        print(f"\n{len(hits)} matches")
        return

    shown = hits[: args.limit] if args.limit else hits
    for c in shown:
        print(f"C{c['id']} [{c['priority']}] ({c['updated_on']}) {c['path']}\n    {c['title']}")
        if args.full:
            for k in ("preconditions", "steps", "expected"):
                if c[k]:
                    print(f"    {k.upper()}: {c[k][:600]}")
    print(f"\n{len(hits)} matches" + (f" (showing {len(shown)})" if len(shown) < len(hits) else ""))


if __name__ == "__main__":
    main()
