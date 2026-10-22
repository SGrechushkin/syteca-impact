"""List all Jira issues of a JQL selection (e.g. a release scope) for pre-sending analysis.

Prints a compact overview grouped by team version (team hotfix, e.g. PAM_H_2026_17 - from Team Version/s
and non-numeric Fix Version/s):
key, type, status, components, summary, Impact_Ekran, TestRail case link.
--out FILE additionally writes the full text of every issue (description, links, comments) to FILE.

Usage:
    py -X utf8 scripts/jira_search.py "project = AC AND fixVersion = 7.28.320"
    py -X utf8 scripts/jira_search.py "https://jira.dev.local/jira/issues/?jql=project%20%3D%20AC%20AND%20fixVersion%20%3D%207.28.320"
    py -X utf8 scripts/jira_search.py "https://jira.dev.local/jira/issues/?filter=12345" --out <scratchpad>/scope.txt
"""
import argparse
from collections import defaultdict
from pathlib import Path

from jira_client import (IMPACT_FIELD, TESTRAIL_FIELD, format_issue, names, search, team_versions,
                         to_jql)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("query", help="JQL, issues URL with jql=, or saved filter URL with filter=")
    ap.add_argument("--out", metavar="FILE", help="write the full text of every issue to FILE")
    args = ap.parse_args()

    jql = to_jql(args.query)
    issues = search(jql)
    print(f"JQL: {jql}\nIssues: {len(issues)}")

    groups = defaultdict(list)
    for issue in issues:
        groups[team_versions(issue["fields"])].append(issue)
    for team, items in sorted(groups.items()):
        print(f"\n=== {team} ({len(items)}) ===")
        for issue in items:
            f = issue["fields"]
            print(f"{issue['key']} [{f['issuetype']['name']} / {f['status']['name']}] "
                  f"({names(f.get('components'))}) {f['summary']}")
            print(f"    IMPACT: {(f.get(IMPACT_FIELD) or '(empty)').strip()}")
            if f.get(TESTRAIL_FIELD):
                print(f"    TESTRAIL: {f[TESTRAIL_FIELD]}")

    if args.out:
        Path(args.out).write_text(
            f"JQL: {jql}\n\n" + "\n\n".join("=" * 80 + "\n" + format_issue(i) for i in issues),
            "utf-8")
        print(f"\nFull text of {len(issues)} issues -> {args.out}")


if __name__ == "__main__":
    main()
