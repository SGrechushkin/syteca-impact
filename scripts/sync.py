"""Download sections and cases of the suite into data/.

Incremental by default: refetches all sections and only the cases updated since the last sync (seconds).
Full sync (few minutes) with --full, when there is no local data yet, or when the last full sync is older
than FULL_EVERY_DAYS - only a full sync drops deleted cases.

Output:
    data/sections.json   raw sections
    data/cases.json      raw cases
    data/index.jsonl     one flattened case per line (id, path, title, priority, text) - used for analysis

Usage:
    py -X utf8 scripts/sync.py [--full]
"""
import argparse
import json
import re
from datetime import datetime, timedelta
from pathlib import Path

from tr_client import PROJECT_ID, SUITE_ID, TestRail

DATA = Path(__file__).resolve().parent.parent / "data"
FULL_EVERY_DAYS = 7
OVERLAP = timedelta(hours=1)  # re-read a bit before the last sync to tolerate clock differences


def clean(text):
    """Strip HTML/markdown noise so cases are easy to search."""
    if not text:
        return ""
    text = re.sub(r"<[^>]+>", " ", str(text))
    text = re.sub(r"!\[\]\([^)]*\)", "[image]", text)
    return re.sub(r"[ \t]+", " ", text).strip()


def steps_text(case):
    """Steps/expected may live in plain fields or in a 'separated steps' field."""
    steps, expected = clean(case.get("custom_steps")), clean(case.get("custom_expected"))
    separated = case.get("custom_steps_separated") or []
    if separated:
        steps = "\n".join(f"{i}. {clean(s.get('content'))}" for i, s in enumerate(separated, 1))
        expected = "\n".join(
            f"{i}. {clean(s.get('expected'))}" for i, s in enumerate(separated, 1) if s.get("expected")
        )
    return steps, expected


def section_paths(sections):
    by_id = {s["id"]: s for s in sections}

    def path(sid):
        parts = []
        while sid:
            s = by_id[sid]
            parts.append(s["name"])
            sid = s.get("parent_id")
        return " / ".join(reversed(parts))

    return {sid: path(sid) for sid in by_id}


def load_state():
    path = DATA / "sync_state.json"
    return json.loads(path.read_text("utf-8")) if path.exists() else {}


def full_fetch(tr, sections):
    # Bulk get_cases exhausts server memory on this instance - fetch section by section instead
    cases = []
    for i, s in enumerate(sections, 1):
        cases.extend(tr.get_all(
            f"get_cases/{PROJECT_ID}&suite_id={SUITE_ID}&section_id={s['id']}", "cases"))
        print(f"\r{i}/{len(sections)} sections, {len(cases)} cases", end="", flush=True)
    print()
    return cases


def incremental_fetch(tr, since):
    # updated_after keeps the result small, so the suite-wide call is safe here
    old = {c["id"]: c for c in json.loads((DATA / "cases.json").read_text("utf-8"))}
    ts = int((datetime.fromisoformat(since) - OVERLAP).timestamp())
    changed = tr.get_all(f"get_cases/{PROJECT_ID}&suite_id={SUITE_ID}&updated_after={ts}", "cases")
    new = sum(c["id"] not in old for c in changed)
    old.update({c["id"]: c for c in changed})
    print(f"{len(changed)} cases changed since {since} ({new} new)")
    return list(old.values())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--full", action="store_true", help="refetch every section (drops deleted cases)")
    args = ap.parse_args()

    tr = TestRail()
    DATA.mkdir(exist_ok=True)
    state = load_state()
    started = datetime.now().isoformat(timespec="seconds")
    last_full = state.get("full_synced_at") or state.get("synced_at")
    full = (args.full or not (DATA / "cases.json").exists() or not last_full
            or datetime.now() - datetime.fromisoformat(last_full) > timedelta(days=FULL_EVERY_DAYS))

    sections = tr.get_all(f"get_sections/{PROJECT_ID}&suite_id={SUITE_ID}", "sections")
    cases = full_fetch(tr, sections) if full else incremental_fetch(tr, state["synced_at"])
    priorities = {p["id"]: p["name"] for p in tr.get("get_priorities")}
    paths = section_paths(sections)

    (DATA / "sections.json").write_text(json.dumps(sections, ensure_ascii=False, indent=1), "utf-8")
    (DATA / "cases.json").write_text(json.dumps(cases, ensure_ascii=False, indent=1), "utf-8")

    with open(DATA / "index.jsonl", "w", encoding="utf-8") as f:
        for c in cases:
            steps, expected = steps_text(c)
            f.write(json.dumps({
                "id": c["id"],
                "path": paths.get(c.get("section_id"), ""),
                "title": c["title"],
                "priority": priorities.get(c.get("priority_id"), c.get("priority_id")),
                "preconditions": clean(c.get("custom_preconds")),
                "steps": steps,
                "expected": expected,
                "refs": c.get("refs"),
                "updated_on": datetime.fromtimestamp(c["updated_on"]).date().isoformat()
                if c.get("updated_on") else None,
            }, ensure_ascii=False) + "\n")

    state = {"synced_at": started, "full_synced_at": started if full else last_full,
             "sections": len(sections), "cases": len(cases)}
    (DATA / "sync_state.json").write_text(json.dumps(state, indent=1), "utf-8")
    print(f"{'Full' if full else 'Incremental'} sync: {len(cases)} cases in {len(sections)} sections -> {DATA}")


if __name__ == "__main__":
    main()
