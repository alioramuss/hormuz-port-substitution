"""
Download IMF PortWatch daily port activity for the ports in config/port_groups.csv.

Uses the public ArcGIS REST service behind PortWatch, one query per port per
year so every request stays under the 1,000 row limit. Standard library only.

Run from the project root:
    python src/fetch_portwatch.py            # 2024-01-01 to latest
    python src/fetch_portwatch.py 2019       # from 2019-01-01
"""

import csv
import json
import sys
import time
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GROUPS = ROOT / "config" / "port_groups.csv"
OUT = ROOT / "data" / "raw" / "portwatch_gulf_ports_2024_2026.csv"

URL = ("https://services9.arcgis.com/weJ1QsnbMYJlCHdG/arcgis/rest/services/"
       "Daily_Ports_Data/FeatureServer/0/query")

FIELDS = [
    "date", "portid", "portname", "country", "ISO3",
    "portcalls_container", "portcalls_dry_bulk", "portcalls_general_cargo",
    "portcalls_roro", "portcalls_tanker", "portcalls_cargo", "portcalls",
    "import_container", "import_dry_bulk", "import_general_cargo", "import_roro",
    "import_tanker", "import_cargo", "import",
    "export_container", "export_dry_bulk", "export_general_cargo", "export_roro",
    "export_tanker", "export_cargo", "export",
]


def query(portid, year, tries=4):
    where = (f"portid='{portid}' AND date >= timestamp '{year}-01-01 00:00:00' "
             f"AND date < timestamp '{year + 1}-01-01 00:00:00'")
    params = urllib.parse.urlencode({
        "where": where, "outFields": ",".join(FIELDS),
        "orderByFields": "date", "resultRecordCount": 1000, "f": "json",
    })
    for attempt in range(tries):
        try:
            with urllib.request.urlopen(f"{URL}?{params}", timeout=60) as r:
                data = json.load(r)
            if "error" in data:
                raise RuntimeError(data["error"])
            if data.get("exceededTransferLimit"):
                raise RuntimeError(f"More than 1000 rows for {portid} {year}")
            return [f["attributes"] for f in data["features"]]
        except Exception as e:  # network hiccups: back off and retry
            if attempt == tries - 1:
                raise
            print(f"  retry {portid} {year}: {e}")
            time.sleep(2 * (attempt + 1))


def main():
    start_year = int(sys.argv[1]) if len(sys.argv) > 1 else 2024
    with open(GROUPS, newline="") as f:
        ports = [row["portid"] for row in csv.DictReader(f)]
    rows = []
    for i, pid in enumerate(ports, 1):
        for year in range(start_year, date.today().year + 1):
            rows.extend(query(pid, year))
        print(f"{i}/{len(ports)} {pid}: {len(rows)} rows so far")
    rows.sort(key=lambda r: (r["portid"], r["date"]))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    print(f"Wrote {len(rows)} rows to {OUT}")


if __name__ == "__main__":
    main()
