---
name: presending
description: Analyze a release scope (Jira JQL / issues or filter link, e.g. fixVersion = 7.28.320) — read every ticket's Impact_Ekran, find impact the developers did not state, and build a "Pre-sending testing <version>" TestRail run. Use when the user gives a JQL selection or asks about pre-sending for a version.
argument-hint: <JQL | Jira issues/filter URL> [ETR ticket] [previous pre-sending run]
---

Follow the "Workflow per release scope (pre-sending)" in CLAUDE.md for: $ARGUMENTS

1. Run `scripts/sync.py`, then `scripts/jira_search.py "<JQL|URL>" --out <scratchpad>/scope_<version>.txt` and read the whole file. Linked tickets outside the scope (e.g. a pentest report) → `scripts/jira_issue.py` when they explain the change.
2. Give the scope table by team version, then the unstated impact (🔴/🟠/🟡) with the ticket and the reason for each.
3. Base: the "Hot_fixes- Pre-sending" cases for the platforms in the scope (from the previous pre-sending run if the user gave it), plus additions for this release.
4. Core-functionality and risk cases per area: TestRail links from the tickets first, then `scripts/search.py` passes. Gaps → extra steps for existing cases (in the report) or new case drafts.
5. Reply in the user's language in the report format from CLAUDE.md; save it to `runs/<NAME>.md` and the IDs to `runs/<NAME>.txt` (NAME = `presending-<version>`), show the dry run of `scripts/create_run.py`.
6. Create the run / new cases with `--yes` ONLY after the user explicitly confirms. Name "Pre-sending testing <version>", description: ETR link (if given) + JQL link. Report the links.
