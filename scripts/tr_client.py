"""Minimal TestRail API v2 client.

Credentials are read from Windows Credential Manager via `keyring`
(service name "syteca-testrail"); they are never printed or written to disk.
"""
import time

import keyring
import requests

try:  # use the Windows certificate store (corporate CA for *.dev.local)
    import truststore
    truststore.inject_into_ssl()
except ImportError:
    pass

BASE_URL = "https://testrail.dev.local"
PROJECT_ID = 9
SUITE_ID = 13
KEYRING_SERVICE = "syteca-testrail"


class TestRailError(Exception):
    pass


class TestRail:
    def __init__(self, base_url=BASE_URL):
        cred = keyring.get_credential(KEYRING_SERVICE, None)
        if cred is None or not cred.password:
            raise TestRailError(
                f"No credentials in Windows Credential Manager for '{KEYRING_SERVICE}'. "
                "Store them with: py -X utf8 scripts/set_credentials.py testrail"
            )
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.session.auth = (cred.username, cred.password)
        self.session.headers["Content-Type"] = "application/json"

    def _url(self, endpoint):
        # TestRail routes through "index.php?/api/v2/..." - extra params are appended with "&"
        return f"{self.base_url}/index.php?/api/v2/{endpoint}"

    def _request(self, method, endpoint, payload=None):
        for attempt in range(5):
            resp = self.session.request(method, self._url(endpoint), json=payload, timeout=60)
            if resp.status_code == 429:  # rate limited
                time.sleep(int(resp.headers.get("Retry-After", 5)))
                continue
            if resp.status_code >= 400:
                try:
                    detail = resp.json().get("error", resp.text)
                except ValueError:
                    detail = resp.text[:300]
                raise TestRailError(f"{method} {endpoint} -> HTTP {resp.status_code}: {detail}")
            return resp.json() if resp.content else None
        raise TestRailError(f"{method} {endpoint}: rate limit retries exhausted")

    def get(self, endpoint):
        return self._request("GET", endpoint)

    def post(self, endpoint, payload):
        return self._request("POST", endpoint, payload)

    def get_all(self, endpoint, key):
        """Fetch every page of a bulk endpoint (handles both paginated and legacy list responses)."""
        items, offset = [], 0
        while True:
            data = self.get(f"{endpoint}&limit=250&offset={offset}")
            if isinstance(data, list):  # older TestRail versions: no pagination
                return data
            page = data.get(key, [])
            items.extend(page)
            if not data.get("_links", {}).get("next") or not page:
                return items
            offset += len(page)
