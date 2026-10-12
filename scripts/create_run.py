"""Create a TestRail run with a selected set of cases.

Dry run by default - prints what would be created. Add --yes to actually create it.

Usage:
    py -X utf8 scripts/create_run.py --name "AC-61577 Some task" --cases 101,102,103
    py -X utf8 scripts/create_run.py --name "AC-61577 Some task" --cases-file runs/AC-61577.txt --yes
    py -X utf8 scripts/create_run.py --update-run 42661 --cases-file runs/ETR-13733.txt   # set exact case list of an existing run
"""
import argparse
import re
import sys
from pathlib import Path

from tr_client import BASE_URL, PROJECT_ID, SUITE_ID, TestRail


def parse_ids(text):
    """Case IDs like C123 or 123; everything after '#' is a comment (whole-line or inline)."""
    text = "\n".join(line.split("#", 1)[0] for line in text.splitlines())
    return sorted({int(x) for x in re.findall(r"\bC?(\d+)\b", text)})


def update_run(run_id, case_ids, yes):
    tr = TestRail()
    run = tr.get(f"get_run/{run_id}")
    tests = tr.get_all(f"get_tests/{run_id}", "tests")
    current = {t["case_id"] for t in tests}
    tested = {t["case_id"] for t in tests if t.get("status_id") != 3}  # 3 = Untested
    removed, added = sorted(current - set(case_ids)), sorted(set(case_ids) - current)
    print(f"Run R{run_id} '{run['name']}': {len(current)} -> {len(case_ids)} cases")
    print(f"Remove ({len(removed)}): " + ", ".join(f"C{i}" for i in removed))
    print(f"Add ({len(added)}): " + ", ".join(f"C{i}" for i in added))
    lost = [i for i in removed if i in tested]
    if lost:
        print("WARNING: these removed cases already have results, the results will be lost: "
              + ", ".join(f"C{i}" for i in lost))
    if not yes:
        print("\nDry run - nothing changed. Re-run with --yes to apply.")
        return
    tr.post(f"update_run/{run_id}", {"include_all": False, "case_ids": case_ids})
    print(f"\nUpdated: {BASE_URL}/index.php?/runs/view/{run_id}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--name", help="run name (required when creating a run)")
    ap.add_argument("--update-run", type=int, metavar="RUN_ID",
                    help="replace the case list of an existing run with the given cases (shows the diff)")
    ap.add_argument("--cases", help="comma-separated case IDs (C123 or 123)")
    ap.add_argument("--cases-file", help="file with case IDs (any separators)")
    ap.add_argument("--description", default="")
    ap.add_argument("--yes", action="store_true", help="actually create the run")
    args = ap.parse_args()

    raw = args.cases or ""
    if args.cases_file:
        raw += " " + Path(args.cases_file).read_text("utf-8")
    case_ids = parse_ids(raw)
    if not case_ids:
        sys.exit("No case IDs given.")

    if args.update_run:
        update_run(args.update_run, case_ids, args.yes)
        return
    if not args.name:
        sys.exit("--name is required to create a run.")

    payload = {
        "suite_id": SUITE_ID,
        "name": args.name,
        "description": args.description,
        "include_all": False,
        "case_ids": case_ids,
    }
    print(f"Project {PROJECT_ID}, suite {SUITE_ID}\nName: {args.name}\nCases ({len(case_ids)}): "
          + ", ".join(f"C{i}" for i in case_ids))

    if not args.yes:
        print("\nDry run - nothing created. Re-run with --yes to create.")
        return

    run = TestRail().post(f"add_run/{PROJECT_ID}", payload)
    print(f"\nCreated run R{run['id']}: {BASE_URL}/index.php?/runs/view/{run['id']}")


if __name__ == "__main__":
    main()
