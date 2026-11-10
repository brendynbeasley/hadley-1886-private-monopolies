"""Small helpers shared by the analysis scripts."""
import pandas as pd

from config import RAW


def fred(series_id, annual=True):
    """Load a FRED series; by default return calendar-year means."""
    x = pd.read_csv(RAW / "fred" / f"{series_id}.csv")
    x.columns = ["date", "value"]
    x["date"] = pd.to_datetime(x["date"])
    x["value"] = pd.to_numeric(x["value"], errors="coerce")
    s = x.set_index("date")["value"].dropna()
    if annual:
        s = s.groupby(s.index.year).mean()
    return s


class Report:
    """Collects printed lines so each script also writes a results file."""

    def __init__(self, path):
        self.path, self.lines = path, []

    def __call__(self, *parts):
        line = " ".join(str(p) for p in parts)
        print(line)
        self.lines.append(line)

    def save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text("\n".join(self.lines) + "\n")
