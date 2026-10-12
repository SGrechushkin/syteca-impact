"""Create new TestRail cases (Text template) from a JSON drafts file.

Dry run by default - prints what would be created. Add --yes to actually create.
Created IDs are written back into the drafts file ("id"), so a re-run never duplicates a case.
New cases are appended to data/index.jsonl so search.py finds them before the next sync.

Drafts file (runs/<KEY>.new.json):
    {
      "refs": "AC-61577",                       # default refs for every case
      "cases": [
        {
          "section": "PAM / Permissions",       # full section path (as search.py prints it) or section id
          "title": "PAM - ... - Check that ...",
          "priority": "High",                   # Low | Medium | High | Critical
          "type": "Manual",                     # TestRail case type name
          "preconditions": "1. ...",
          "steps": "1. ...\n2. ...",
          "expected": "..."
        }
      ]
    }

Usage:
    py -X utf8 scripts/create_cases.py runs/AC-61577.new.json
    py -X utf8 scripts/create_cases.py runs/AC-61577.new.json --yes --add-to-run 42661
"""
import argparse
import json
import sys
import time
from datetime import date
from pathlib import Path

import requests

from sync import DATA, section_paths
from tr_client import BASE_URL, PROJECT_ID, SUITE_ID, TestRail, TestRailError

TEXT_TEMPLATE_ID = 1
MAX_TITLE = 250


def resolve_sections(drafts):
    sections = json.loads((DATA / "sections.json").read_text("utf-8"))
    paths = section_paths(sections)
    by_path = {p.lower(): sid for sid, p in paths.items()}
    resolved = {}
    for c in drafts:
        sec = c["section"]
        if isinstance(sec, int) or str(sec).isdigit():
            sid = int(sec)
            if sid not in paths:
                sys.exit(f"Unknown section id {sid} for: {c['title']}")
        else:
            sid = by_path.get(sec.strip().lower())
            if sid is None:
                sys.exit(f"Unknown section path '{sec}' for: {c['title']}")
        resolved[id(c)] = (sid, paths[sid])
    return resolved


def find_by_title(tr, section_id, title):
    cases = tr.get_all(f"get_cases/{PROJECT_ID}&suite_id={SUITE_ID}&section_id={section_id}", "cases")
    return next((c["id"] for c in cases if c["title"].strip() == title.strip()), None)


def add_to_run(tr, run_id, new_ids):
    run = tr.get(f"get_run/{run_id}")
    if run.get("include_all"):
        print(f"Run R{run_id} includes all cases - nothing to add.")
        return
    existing = [t["case_id"] for t in tr.get_all(f"get_tests/{run_id}", "tests")]
    merged = sorted(set(existing) | set(new_ids))
    tr.post(f"update_run/{run_id}", {"include_all": False, "case_ids": merged})
    print(f"Run R{run_id}: {len(existing)} -> {len(merged)} cases  {BASE_URL}/index.php?/runs/view/{run_id}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("file")
    ap.add_argument("--yes", action="store_true", help="actually create the cases")
    ap.add_argument("--add-to-run", type=int, metavar="RUN_ID", help="also add the cases to this run")
    args = ap.parse_args()

    path = Path(args.file)
    doc = json.loads(path.read_text("utf-8"))
    drafts = doc["cases"]
    too_long = [c["title"] for c in drafts if len(c["title"]) > MAX_TITLE]
    if too_long:
        sys.exit("Titles longer than %d chars:\n" % MAX_TITLE
                 + "\n".join(f"  ({len(t)}) {t}" for t in too_long))
    sections = resolve_sections(drafts)

    tr = TestRail()
    priorities = {p["name"].lower(): p["id"] for p in tr.get("get_priorities")}
    types = {t["name"].lower(): t["id"] for t in tr.get("get_case_types")}

    todo = []
    for c in drafts:
        sid, spath = sections[id(c)]
        prio = priorities.get(c.get("priority", "Medium").lower())
        ctype = types.get(c.get("type", "Manual").lower())
        if prio is None or ctype is None:
            sys.exit(f"Unknown priority/type for: {c['title']}")
        mark = f"exists C{c['id']}" if c.get("id") else "NEW"
        print(f"[{mark}] [{c.get('priority', 'Medium')}] {spath}\n    ({len(c['title'])}) {c['title']}")
        if not c.get("id"):
            todo.append((c, sid, {
                "title": c["title"],
                "template_id": TEXT_TEMPLATE_ID,
                "type_id": ctype,
                "priority_id": prio,
                "refs": c.get("refs", doc.get("refs", "")),
                "custom_preconds": c.get("preconditions", ""),
                "custom_steps": c.get("steps", ""),
                "custom_expected": c.get("expected", ""),
            }))
    print(f"\n{len(todo)} to create, {len(drafts) - len(todo)} already created")

    if not args.yes:
        print("Dry run - nothing created. Re-run with --yes to create.")
        return

    with open(DATA / "index.jsonl", "a", encoding="utf-8") as index:
        for c, sid, payload in todo:
            # the server sometimes creates the case but answers with a timeout/500,
            # so look for the same title in the section before and after every attempt
            case_id = find_by_title(tr, sid, c["title"])
            if case_id:
                print(f"Already in TestRail C{case_id} - not creating again")
            else:
                try:
                    case_id = tr.post(f"add_case/{sid}", payload)["id"]
                    print(f"Created C{case_id}: {BASE_URL}/index.php?/cases/view/{case_id}")
                except (TestRailError, requests.RequestException) as e:
                    time.sleep(10)
                    case_id = find_by_title(tr, sid, c["title"])
                    if not case_id:
                        sys.exit(f"Failed to create '{c['title']}': {e}\nRe-run the same command to retry.")
                    print(f"Server error, but the case was created: C{case_id}")
            c["id"] = case_id
            # save after every case so a failure halfway never leads to duplicates
            path.write_text(json.dumps(doc, ensure_ascii=False, indent=2), "utf-8")
            index.write(json.dumps({
                "id": case_id, "path": sections[id(c)][1], "title": c["title"],
                "priority": c.get("priority", "Medium"), "preconditions": payload["custom_preconds"],
                "steps": payload["custom_steps"], "expected": payload["custom_expected"],
                "refs": payload["refs"], "updated_on": date.today().isoformat(),
            }, ensure_ascii=False) + "\n")

    if args.add_to_run:
        all_ids = [c["id"] for c in drafts if c.get("id")]
        add_to_run(tr, args.add_to_run, all_ids)


if __name__ == "__main__":
    main()
