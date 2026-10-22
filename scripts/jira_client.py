"""Shared Jira access for jira_issue.py and jira_search.py.

Credentials are read from Windows Credential Manager (service "syteca-jira").
"""
import re
import sys
from urllib.parse import parse_qs, urlparse

import keyring
import requests

try:
    import truststore
    truststore.inject_into_ssl()
except ImportError:
    pass

JIRA_URL = "https://jira.dev.local/jira"
KEYRING_SERVICE = "syteca-jira"
IMPACT_FIELD = "customfield_14800"  # "Impact_Ekran" - the basis for test selection
TEAM_FIELD = "customfield_15009"  # "Team"
TEAM_VERSION_FIELD = "customfield_16300"  # "Team Version/s", e.g. PAM_H_2026_17, PEDM_HOTFIX_10
REGRESSION_FIELD = "customfield_15104"  # "Regression"
TESTRAIL_FIELD = "customfield_14100"  # "Link to test rail case"
FIELDS = ",".join([
    "summary", "description", "comment", "issuetype", "status", "priority", "components",
    "fixVersions", "labels", "issuelinks",
    IMPACT_FIELD, TEAM_FIELD, TEAM_VERSION_FIELD, REGRESSION_FIELD, TESTRAIL_FIELD,
])


def _auth():
    cred = keyring.get_credential(KEYRING_SERVICE, None)
    if cred is None:
        sys.exit("No Jira credentials. Run: py -X utf8 scripts/set_credentials.py jira")
    return cred.username, cred.password


def get(path, params=None):
    resp = requests.get(f"{JIRA_URL}/rest/api/2/{path}", params=params, auth=_auth(), timeout=60)
    if resp.status_code >= 400:
        sys.exit(f"Jira {path} -> HTTP {resp.status_code}: {resp.text[:300]}")
    return resp.json()


def get_issue(key):
    return get(f"issue/{key}", {"fields": FIELDS})


def to_jql(arg):
    """JQL from a plain JQL string, an issues URL (?jql=...) or a saved filter URL (?filter=ID)."""
    if not arg.startswith("http"):
        return arg
    query = parse_qs(urlparse(arg).query)
    if "jql" in query:
        return query["jql"][0]
    if "filter" in query:
        return get(f"filter/{query['filter'][0]}")["jql"]
    match = re.search(r"[A-Z][A-Z0-9]+-\d+", arg)
    if match:
        return f"key = {match.group(0)}"
    sys.exit(f"No jql= or filter= in the URL: {arg}")


def search(jql):
    issues, start = [], 0
    while True:
        page = get("search", {"jql": jql, "fields": FIELDS, "startAt": start, "maxResults": 100})
        issues += page["issues"]
        start += len(page["issues"])
        if not page["issues"] or start >= page["total"]:
            return issues


def names(values, attr="name"):
    return ", ".join(v.get(attr, "") for v in values or [])


def team_versions(f):
    """Team hotfix versions (PAM_H_2026_17, PEDM_HOTFIX_10): Team Version/s plus non-numeric Fix Version/s."""
    found = [v["name"] for v in (f.get(TEAM_VERSION_FIELD) or []) + (f.get("fixVersions") or [])
             if not re.fullmatch(r"[\d.]+", v["name"])]
    return ", ".join(dict.fromkeys(found)) or "(no team version)"


def format_issue(issue):
    """Full text of an issue: impact, metadata, links, description, comments."""
    f = issue["fields"]
    lines = [
        f"KEY: {issue['key']}",
        f"SUMMARY: {f['summary']}",
        f"\n>>> IMPACT_EKRAN: {f.get(IMPACT_FIELD) or '(empty - ask the user for the impact)'}\n",
        f"TYPE: {f['issuetype']['name']}   STATUS: {f['status']['name']}   "
        f"PRIORITY: {(f.get('priority') or {}).get('name', '')}",
        f"COMPONENTS: {names(f.get('components'))}",
        f"FIX VERSIONS: {names(f.get('fixVersions'))}",
        f"TEAM: {(f.get(TEAM_FIELD) or {}).get('name', '')}   TEAM VERSIONS: {team_versions(f)}",
        f"REGRESSION: {names(f.get(REGRESSION_FIELD), 'value')}",
        f"TESTRAIL CASE: {f.get(TESTRAIL_FIELD) or ''}",
        f"LABELS: {', '.join(f.get('labels') or [])}",
    ]
    for link in f.get("issuelinks") or []:
        other = link.get("outwardIssue") or link.get("inwardIssue")
        if other:
            lines.append(f"LINK: {link['type']['name']} {other['key']} - {other['fields']['summary']}")
    lines.append(f"\nDESCRIPTION:\n{f.get('description') or ''}")
    for c in (f.get("comment") or {}).get("comments", []):
        lines.append(f"\n--- COMMENT by {c['author']['displayName']} ({c['created'][:10]}):\n{c['body']}")
    return "\n".join(lines)
