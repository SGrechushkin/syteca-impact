"""Store TestRail / Jira credentials in Windows Credential Manager.

Run it and type the login/password when asked - never put them into this file.

Usage:
    py -X utf8 scripts/set_credentials.py testrail
    py -X utf8 scripts/set_credentials.py jira
"""
import getpass
import sys

import keyring

SERVICES = {
    "testrail": "syteca-testrail",
    "jira": "syteca-jira",
}

if len(sys.argv) != 2 or sys.argv[1] not in SERVICES:
    sys.exit(__doc__)

name = sys.argv[1]
service = SERVICES[name]
username = input(f"{name} login: ").strip()
secret = getpass.getpass(f"{name} password (input is hidden): ")
if not username or not secret:
    sys.exit("Empty login or password - nothing saved.")
keyring.set_password(service, username, secret)
print(f"Saved to Windows Credential Manager as '{service}'.")
