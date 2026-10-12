"""Download all sections and cases of the suite into data/.

Output:
    data/sections.json   raw sections
    data/cases.json      raw cases
    data/index.jsonl     one flattened case per line (id, path, title, priority, text) - used for analysis
"""
import json
import re
from datetime import datetime
from pathlib import Path

from tr_client import PROJECT_ID, SUITE_ID, TestRail

DATA = Path(__file__).resolve().parent.parent / "data"


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


def main():
    tr = TestRail()
    DATA.mkdir(exist_ok=True)

    sections = tr.get_all(f"get_sections/{PROJECT_ID}&suite_id={SUITE_ID}", "sections")
    # Bulk get_cases exhausts server memory on this instance - fetch section by section instead
    cases = []
    for i, s in enumerate(sections, 1):
        cases.extend(tr.get_all(
            f"get_cases/{PROJECT_ID}&suite_id={SUITE_ID}&section_id={s['id']}", "cases"))
        print(f"\r{i}/{len(sections)} sections, {len(cases)} cases", end="", flush=True)
    print()
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

    state = {"synced_at": datetime.now().isoformat(timespec="seconds"),
             "sections": len(sections), "cases": len(cases)}
    (DATA / "sync_state.json").write_text(json.dumps(state, indent=1), "utf-8")
    print(f"Synced {len(cases)} cases in {len(sections)} sections -> {DATA}")


if __name__ == "__main__":
    main()
