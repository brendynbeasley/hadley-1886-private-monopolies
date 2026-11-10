"""Shared settings: paths, the firm sample, and the FRED series used."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"
RESULTS = ROOT / "results"
FIGURES = ROOT / "figures"
DOCS = ROOT / "docs"
PAPER = ROOT / "paper"

# SEC Central Index Key -> (short name, mode). Rail firms own their track;
# trucking and air firms operate on publicly provided infrastructure.
FIRMS = {
    100885: ("Union Pacific", "Rail"),
    277948: ("CSX", "Rail"),
    702165: ("Norfolk Southern", "Rail"),
    934612: ("BNSF", "Rail"),
    54480: ("Kansas City Southern", "Rail"),
    728535: ("J.B. Hunt", "Truck"),
    1492691: ("Knight-Swift", "Truck"),
    793074: ("Werner", "Truck"),
    878927: ("Old Dominion", "Truck"),
    1692063: ("Schneider", "Truck"),
    799233: ("Heartland Express", "Truck"),
    1177702: ("Saia", "Truck"),
    894405: ("ArcBest", "Truck"),
    799167: ("Marten", "Truck"),
    27904: ("Delta", "Air"),
    100517: ("United", "Air"),
    6201: ("American", "Air"),
    92380: ("Southwest", "Air"),
    766421: ("Alaska Air", "Air"),
    1158463: ("JetBlue", "Air"),
}

# Knight-Swift reports as a combined company only from the 2017 merger.
FIRST_YEAR = {"Knight-Swift": 2017}

FRED_SERIES = {
    # Modern price indexes
    "PCU482111482111": "PPI: line-haul railroads (1969-)",
    "PCU484121484121": "PPI: general freight trucking, long-distance truckload (2003-)",
    "CUSR0000SETG01": "CPI: airline fares, seasonally adjusted (1989-)",
    "CPIAUCSL": "CPI: all items, seasonally adjusted (1947-)",
    "CPIAUCNS": "CPI: all items, not seasonally adjusted (1913-)",
    # NBER Macrohistory Database (historical railroad series)
    "A0303FUSA259NNBR": "Revenue per freight ton-mile, thirteen railroads (1865-1890)",
    "A0303DUSA259NNBR": "Revenue per freight ton-mile, all railroads (1882-1911)",
    "A0303BUSA259NNBR": "Revenue per freight ton-mile, all railroads (1888-1935)",
    "M033ACUSM270NNBR": "Revenue per freight ton-mile, Class I railroads (1920-1956)",
    "M04051USM324NNBR": "Index of the general price level (1860-1939)",
    "A02F2AUSA374NNBR": "Miles of railroad built (1830-1952)",
    "A02133USA581NNBR": "Total track mileage (1890-1916)",
    "A02F3AUSA581NNBR": "Total track mileage (1916-1942)",
    "M11005USM293NNBR": "American railroad stock prices, dollars per share (1855-1937)",
    "M03016USM144NNBR": "Total operating revenue, Class I railroads (1907-1963)",
    "M03040USM144NNBR": "Total operating expenses, Class I railroads (1907-1963)",
}
