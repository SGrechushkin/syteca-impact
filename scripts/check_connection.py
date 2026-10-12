"""Verify TestRail access and print project / suite / field info."""
from tr_client import PROJECT_ID, SUITE_ID, TestRail

tr = TestRail()
print(f"Login: {tr.session.auth[0]}")

project = tr.get(f"get_project/{PROJECT_ID}")
print(f"Project {PROJECT_ID}: {project['name']} (suite_mode={project.get('suite_mode')})")

suite = tr.get(f"get_suite/{SUITE_ID}")
print(f"Suite {SUITE_ID}: {suite['name']} (project_id={suite['project_id']})")
if suite["project_id"] != PROJECT_ID:
    print(f"WARNING: suite {SUITE_ID} belongs to project {suite['project_id']}, not {PROJECT_ID}")

print("\nCase fields:")
for f in tr.get("get_case_fields"):
    print(f"  {f['system_name']:<35} {f['label']}")

print("\nPriorities:")
for p in tr.get("get_priorities"):
    print(f"  {p['id']}: {p['name']}")
