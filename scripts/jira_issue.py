"""Print a Jira issue (summary, description, comments) for impact analysis.

Credentials are read from Windows Credential Manager (service "syteca-jira").

Usage:
    py -X utf8 scripts/jira_issue.py AC-61577
    py -X utf8 scripts/jira_issue.py https://jira.dev.local/jira/browse/AC-61577
"""
import re
import sys

from jira_client import format_issue, get_issue

if len(sys.argv) != 2:
    sys.exit(__doc__)
match = re.search(r"[A-Z][A-Z0-9]+-\d+", sys.argv[1])
if not match:
    sys.exit(f"Not a Jira key: {sys.argv[1]}")

print(format_issue(get_issue(match.group(0))))
