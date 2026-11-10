"""Download raw inputs from FRED and SEC EDGAR into data/raw/.

SEC EDGAR asks automated clients to identify themselves. Set SEC_USER_AGENT
to something like "Your Name your.email@example.com" before running.
"""
import json
import os
import sys
import time
import urllib.request

from config import FIRMS, FRED_SERIES, RAW

FRED_URL = "https://fred.stlouisfed.org/graph/fredgraph.csv?id={}"
SEC_URL = "https://data.sec.gov/api/xbrl/companyfacts/CIK{:010d}.json"


def get(url, headers=None):
    req = urllib.request.Request(url, headers=headers or {})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.read()
        except Exception as exc:  # network hiccups: back off and retry
            if attempt == 3:
                raise
            print(f"  retry {url} ({exc})")
            time.sleep(2 ** (attempt + 1))


def fetch_fred():
    out = RAW / "fred"
    out.mkdir(parents=True, exist_ok=True)
    for sid in FRED_SERIES:
        (out / f"{sid}.csv").write_bytes(get(FRED_URL.format(sid)))
        print(f"FRED {sid}")


def fetch_sec():
    agent = os.environ.get("SEC_USER_AGENT")
    if not agent:
        sys.exit("Set SEC_USER_AGENT, e.g. 'Jane Doe jane@example.com'")
    out = RAW / "sec"
    out.mkdir(parents=True, exist_ok=True)
    for cik, (name, _) in FIRMS.items():
        body = get(SEC_URL.format(cik), {"User-Agent": agent})
        json.loads(body)  # fail early on a bad payload
        (out / f"{cik}.json").write_bytes(body)
        print(f"SEC {cik} {name}")
        time.sleep(0.2)  # stay well under the SEC's 10 requests/second limit


if __name__ == "__main__":
    fetch_fred()
    fetch_sec()
