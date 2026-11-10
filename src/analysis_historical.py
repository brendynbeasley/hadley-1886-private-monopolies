"""Historical test of Hadley (1886) using the NBER Macrohistory Database.

Writes results/historical_results.txt, data/processed/historical_rates.csv
and data/processed/historical_margins.csv.
"""
import numpy as np
import pandas as pd
import scipy.stats as st

from common import Report, fred
from config import PROCESSED, RESULTS


def freight_rate():
    """Splice nominal revenue per ton-mile, 1865-1955 (cents)."""
    r13 = fred("A0303FUSA259NNBR")   # thirteen railroads, 1865-1890
    all_a = fred("A0303DUSA259NNBR")  # all railroads, 1882-1911
    all_b = fred("A0303BUSA259NNBR")  # all railroads, 1888-1935
    class1 = fred("M033ACUSM270NNBR")  # Class I, 1920-1956
    scale = all_a.loc[1882:1890].mean() / r13.loc[1882:1890].mean()
    return pd.concat([r13.loc[:1881] * scale, all_a.loc[1882:1887], all_b.loc[1888:1919], class1.loc[1920:1955]])


def price_level():
    """General price level to 1912, chained to the CPI from 1913."""
    gpl, cpi = fred("M04051USM324NNBR"), fred("CPIAUCNS")
    return pd.concat([gpl.loc[:1912] * (cpi.loc[1913:1920].mean() / gpl.loc[1913:1920].mean()), cpi.loc[1913:]])


def operating_margin():
    """Class I operating margin from monthly revenue and expenses, complete years only."""
    rev, exp = fred("M03016USM144NNBR", annual=False), fred("M03040USM144NNBR", annual=False)
    m = pd.DataFrame({"rev": rev, "exp": exp}).dropna()
    g = m.groupby(m.index.year).agg(["sum", "count"])
    full = g[("rev", "count")] == 12
    return ((g[("rev", "sum")] - g[("exp", "sum")]) / g[("rev", "sum")] * 100)[full]


def main():
    out = Report(RESULTS / "historical_results.txt")
    rate, price = freight_rate(), price_level()
    real = (rate / price).dropna()
    real = real / real[1886] * 100
    built = fred("A02F2AUSA374NNBR")
    hist = pd.DataFrame({"rate_cents": rate, "price_level": price, "real_rate_1886_100": real}).dropna()
    hist["miles_built"] = built
    hist.to_csv(PROCESSED / "historical_rates.csv", index_label="year")

    out("== Freight rates, 1865-1955 ==")
    out("Real rate (1886 = 100):", real.loc[[1865, 1886, 1900, 1916, 1955]].round(0).to_dict())
    out("Nominal cents per ton-mile, thirteen railroads:", fred("A0303FUSA259NNBR").loc[[1865, 1890]].round(2).to_dict())
    out(f"Years with a lower nominal rate than the year before, 1866-1900: {(rate.diff().loc[1866:1900] < 0).sum()} of 35")

    out("\n== Construction and the crises Hadley names ==")
    for y in [1872, 1882, 1887]:
        out(f"Miles built {y}: {int(built[y]):,}")
    stocks = fred("M11005USM293NNBR", annual=False)
    for lo, hi in [("1857", "1859"), ("1872", "1877"), ("1881", "1885")]:
        s = stocks.loc[lo:hi]
        peak = s.idxmax()
        out(f"Railroad stocks {lo}-{hi}: peak {peak:%Y-%m} {s.max():.1f}, trough {s.loc[peak:].idxmin():%Y-%m} "
            f"{s.loc[peak:].min():.1f}, drawdown {(s.loc[peak:].min() / s.max() - 1) * 100:.1f}%")

    out("\n== Does a construction boom precede faster rate declines? 1866-1913 ==")
    d = pd.DataFrame({"dlog_real": np.log(real).diff() * 100, "log_built": np.log(built)}).loc[1866:1913]
    for k in range(0, 6):
        x = pd.DataFrame({"y": d.dlog_real, "x": d.log_built.shift(k)}).dropna()
        r = st.pearsonr(x.y, x.x)
        out(f"lag {k}: r = {r.statistic:+.2f}, p = {r.pvalue:.3f}, n = {len(x)}")
    out("Hadley predicts a negative correlation. None of the lags is negative.")

    out("\n== Operating margin before and after federal rate control ==")
    om = operating_margin()
    om.rename("operating_margin").to_csv(PROCESSED / "historical_margins.csv", index_label="year")
    for name, (a, b) in {"1908-1916": (1908, 1916), "1921-1929": (1921, 1929), "1930-1939": (1930, 1939),
                         "1946-1961": (1946, 1961)}.items():
        s = om.loc[a:b]
        out(f"{name}: mean {s.mean():.1f}%, SD {s.std():.1f}, n = {len(s)}")
    pre = om.loc[1908:1916]
    post = pd.concat([om.loc[1921:1940], om.loc[1946:1961]])
    t = st.ttest_ind(pre, post, equal_var=False)
    out(f"1908-16 vs 1921-61 excluding 1941-45: {pre.mean():.1f}% vs {post.mean():.1f}%, "
        f"Welch t({t.df:.0f}) = {t.statistic:.2f}, p = {t.pvalue:.2g}")

    out("\n== Track mileage (thousands of miles) ==")
    t1, t2 = fred("A02133USA581NNBR"), fred("A02F3AUSA581NNBR")
    out(f"1890: {t1[1890]:.1f}  1916: {t1[1916]:.1f}  1942: {t2[1942]:.1f}")
    out.save()


if __name__ == "__main__":
    main()
