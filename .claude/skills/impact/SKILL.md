---
name: impact
description: Build a TestRail run for a Jira ticket from its Impact_Ekran field. Use when the user gives a Jira key/link (e.g. AC-61577) or impact text and wants tests picked or a run created.
argument-hint: <JIRA-KEY or URL> [run name]
---

Follow the "Workflow per impact" in CLAUDE.md for: $ARGUMENTS

1. If `data/sync_state.json` is older than 1 day — run `scripts/sync.py` first.
2. `scripts/jira_issue.py <KEY>` → take Impact_Ekran as the scope. Empty → ask the user for the impact.
3. Search with several `scripts/search.py` passes (synonyms, role/permission, adjacent flows, opposite side). Wide passes: `--by-section` first, then `--path`. Read case details with `scripts/show.py`.
4. Reply in Russian with: P1 / P2 / P3 tables (case + one-line reason), gaps, duplicates, suspected outdated.
5. Save IDs to `runs/<KEY>.txt` with tier comments and show the dry run of `scripts/create_run.py`.
6. For gaps: draft new cases in `runs/<KEY>.new.json` following "Rules for new cases" in CLAUDE.md (existing folder by meaning, neighbour style, never edit existing cases) and show the dry run of `scripts/create_cases.py`.
7. Create the run / new cases with `--yes` ONLY after the user explicitly confirms. Run name: the name the user gave, otherwise "<KEY> <summary>". Description: "<KEY> | Impact_Ekran: <impact>". Add created cases to the run with `--add-to-run`. Report the links.
