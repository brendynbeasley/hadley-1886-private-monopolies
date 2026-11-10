"""Build the firm-year panel from SEC EDGAR XBRL company facts.

Output: data/processed/firm_panel.csv, one row per firm and fiscal year.
Fiscal years ending in the first half of a calendar year are assigned to
the previous year.
"""
import datetime as dt
import json

import numpy as np
import pandas as pd

from config import FIRMS, FIRST_YEAR, PROCESSED, RAW

REVENUE_TAGS = [
    "Revenues",
    "RevenueFromContractWithCustomerExcludingAssessedTax",
    "RevenueFromContractWithCustomerIncludingAssessedTax",
    "SalesRevenueServicesNet",
    "SalesRevenueNet",
]
PPE_TAGS = [
    "PropertyPlantAndEquipmentNet",
    "PropertyPlantAndEquipmentAndFinanceLeaseRightOfUseAssetAfterAccumulatedDepreciationAndAmortization",
]


def annual(facts, tags, instant=False, pick_max=False):
    """Annual USD values from 10-K filings, keyed by fiscal year.

    Earlier tags take priority. Within a tag, the latest filing wins, so
    restated figures replace originals. With pick_max, a larger value under
    a later tag replaces a smaller one (some filers split revenue across
    tags in different years).
    """
    out = {}
    for tag in tags:
        if tag not in facts:
            continue
        for u in facts[tag]["units"].get("USD", []):
            if not u.get("form", "").startswith("10-K"):
                continue
            end = dt.date.fromisoformat(u["end"])
            if not instant:
                if "start" not in u:
                    continue
                days = (end - dt.date.fromisoformat(u["start"])).days
                if not 350 <= days <= 380:
                    continue
            year = end.year if end.month > 6 else end.year - 1
            prev = out.get(year)
            if (
                prev is None
                or (prev[2] == tag and u["filed"] > prev[1])
                or (pick_max and prev[2] != tag and u["val"] > prev[0])
            ):
                out[year] = (u["val"], u["filed"], tag)
    return {k: v[0] for k, v in out.items()}


def main():
    rows = []
    for cik, (name, mode) in FIRMS.items():
        facts = json.load(open(RAW / "sec" / f"{cik}.json"))["facts"]["us-gaap"]
        rev = annual(facts, REVENUE_TAGS, pick_max=True)
        oi = annual(facts, ["OperatingIncomeLoss"])
        ppe = annual(facts, PPE_TAGS, instant=True)
        assets = annual(facts, ["Assets"], instant=True)
        for y in sorted(rev):
            rows.append(dict(cik=cik, firm=name, mode=mode, year=y, revenue=rev[y],
                             op_income=oi.get(y), ppe=ppe.get(y), assets=assets.get(y)))
    df = pd.DataFrame(rows)
    df = df[(df.year >= 2007) & (df.year <= 2025)]
    for firm, y0 in FIRST_YEAR.items():
        df = df[~((df.firm == firm) & (df.year < y0))]
    df = df.dropna(subset=["op_income"])
    df["margin"] = df.op_income / df.revenue * 100
    df["roa"] = df.op_income / df.assets * 100
    df["ppe_rev"] = df.ppe / df.revenue
    df["ppe_assets"] = df.ppe / df.assets
    df["log_ppe_rev"] = np.log(df.ppe_rev)
    PROCESSED.mkdir(parents=True, exist_ok=True)
    df.to_csv(PROCESSED / "firm_panel.csv", index=False)
    print(f"firm_panel.csv: {len(df)} firm-years, {df.firm.nunique()} firms, {df.year.min()}-{df.year.max()}")


if __name__ == "__main__":
    main()
