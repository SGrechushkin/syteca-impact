"""Print a Jira issue (summary, description, comments) for impact analysis.

Credentials are read from Windows Credential Manager (service "syteca-jira").

Usage:
    py -X utf8 scripts/jira_issue.py AC-61577
    py -X utf8 scripts/jira_issue.py https://jira.dev.local/jira/browse/AC-61577
"""
import re
import sys

import keyring
import requests

try:
    import truststore
    truststore.inject_into_ssl()
except ImportError:
    pass

JIRA_URL = "https://jira.dev.local/jira"
IMPACT_FIELD = "customfield_14800"  # "Impact_Ekran" - the basis for test selection
KEYRING_SERVICE = "syteca-jira"

if len(sys.argv) != 2:
    sys.exit(__doc__)
match = re.search(r"[A-Z][A-Z0-9]+-\d+", sys.argv[1])
if not match:
    sys.exit(f"Not a Jira key: {sys.argv[1]}")
key = match.group(0)

cred = keyring.get_credential(KEYRING_SERVICE, None)
if cred is None:
    sys.exit("No Jira credentials. Run: py -X utf8 scripts/set_credentials.py jira")

resp = requests.get(
    f"{JIRA_URL}/rest/api/2/issue/{key}",
    params={"fields": f"summary,description,comment,issuetype,status,components,fixVersions,labels,issuelinks,{IMPACT_FIELD}"},
    auth=(cred.username, cred.password),
    timeout=60,
)
if resp.status_code >= 400:
    sys.exit(f"Jira {key} -> HTTP {resp.status_code}: {resp.text[:300]}")
f = resp.json()["fields"]

print(f"KEY: {key}")
print(f"SUMMARY: {f['summary']}")
print(f"\n>>> IMPACT_EKRAN: {f.get(IMPACT_FIELD) or '(empty - ask the user for the impact)'}\n")
print(f"TYPE: {f['issuetype']['name']}   STATUS: {f['status']['name']}")
print(f"COMPONENTS: {', '.join(c['name'] for c in f.get('components') or [])}")
print(f"FIX VERSIONS: {', '.join(v['name'] for v in f.get('fixVersions') or [])}")
print(f"LABELS: {', '.join(f.get('labels') or [])}")
for link in f.get("issuelinks") or []:
    other = link.get("outwardIssue") or link.get("inwardIssue")
    if other:
        print(f"LINK: {link['type']['name']} {other['key']} - {other['fields']['summary']}")
print(f"\nDESCRIPTION:\n{f.get('description') or ''}")
for c in (f.get("comment") or {}).get("comments", []):
    print(f"\n--- COMMENT by {c['author']['displayName']} ({c['created'][:10]}):\n{c['body']}")
