"""Modern test of Hadley (1886): rail vs trucking vs air, fiscal 2009-2025.

Writes results/modern_results.txt, data/processed/firm_means.csv and
data/processed/prices_annual.csv.
"""
import numpy as np
import pandas as pd
import scipy.stats as st
import statsmodels.formula.api as smf
from statsmodels.stats.diagnostic import het_breuschpagan
from statsmodels.stats.power import TTestIndPower

from common import Report, fred
from config import PROCESSED, RESULTS

MODES = ["Rail", "Truck", "Air"]


def clustered(formula, data):
    return smf.ols(formula, data).fit(cov_type="cluster", cov_kwds={"groups": data["cik"]}, use_t=True)


def coef_table(m):
    keep = [k for k in m.params.index if "year" not in k]
    ci = m.conf_int()
    return pd.DataFrame({"b": m.params[keep], "se": m.bse[keep], "t": m.tvalues[keep],
                         "p": m.pvalues[keep], "ci_lo": ci.loc[keep, 0], "ci_hi": ci.loc[keep, 1]}).round(3)


def main():
    out = Report(RESULTS / "modern_results.txt")
    panel = pd.read_csv(PROCESSED / "firm_panel.csv")
    df = panel[(panel.year >= 2009) & (panel.year <= 2025)].copy()

    out("== Sample ==")
    out(f"Firm-years: {len(df)}  Firms: {df.firm.nunique()}  Years: {df.year.min()}-{df.year.max()}")
    out(df.groupby("mode").agg(firms=("firm", "nunique"), n=("margin", "size"), margin=("margin", "mean"),
                               margin_sd=("margin", "std"), roa=("roa", "mean"), ppe_per_rev=("ppe_rev", "mean"))
        .round(2).to_string())

    # Firm-level means: one observation per firm, so independence holds.
    def sd_ex2020(s):
        return s[df.loc[s.index, "year"] != 2020].std()

    fm = df.groupby(["mode", "firm"]).agg(n=("margin", "size"), margin=("margin", "mean"), sd=("margin", "std"),
                                          sd_ex2020=("margin", sd_ex2020), roa=("roa", "mean"),
                                          ppe_rev=("ppe_rev", "mean")).reset_index()
    fm.to_csv(PROCESSED / "firm_means.csv", index=False)
    out("\n== Firm means ==")
    out(fm.round(2).to_string(index=False))

    out("\n== Firm-level tests (n = 20) ==")
    groups = {m: fm[fm["mode"] == m] for m in MODES}
    for var in ["margin", "roa", "sd", "sd_ex2020"]:
        a = [groups[m][var].values for m in MODES]
        f = st.f_oneway(*a)
        h = st.kruskal(*a)
        out(f"{var:10s} ANOVA F(2,17) = {f.statistic:.2f}, p = {f.pvalue:.4g} | Kruskal-Wallis H = {h.statistic:.2f}, p = {h.pvalue:.4g}")
    a = [groups[m]["margin"].values for m in MODES]
    allv = np.concatenate(a)
    eta2 = sum(len(x) * (x.mean() - allv.mean()) ** 2 for x in a) / ((allv - allv.mean()) ** 2).sum()
    rail, other = a[0], np.concatenate(a[1:])
    sp = np.sqrt(((len(rail) - 1) * rail.var(ddof=1) + (len(other) - 1) * other.var(ddof=1)) / (len(rail) + len(other) - 2))
    out(f"Margin eta-squared = {eta2:.3f}; Cohen's d (rail vs others) = {(rail.mean() - other.mean()) / sp:.2f}")
    out("Shapiro-Wilk p by group (Rail, Truck, Air):", [round(st.shapiro(x).pvalue, 3) for x in a])
    out(f"Levene p = {st.levene(*a).pvalue:.3f}")

    out("\n== Power (firm level, 5 rail vs 15 other, alpha = .05, two-tailed) ==")
    pw = TTestIndPower()
    d80 = pw.solve_power(nobs1=5, ratio=3, alpha=0.05, power=0.8)
    out(f"Minimum detectable d at 80% power: {d80:.2f}")
    out(f"Firms per group needed for d = 0.8 at 80% power: {pw.solve_power(effect_size=0.8, alpha=0.05, power=0.8):.1f}")
    roa_sd = np.sqrt(((4) * groups['Rail'].roa.var() + (14) * pd.concat([groups['Truck'], groups['Air']]).roa.var()) / 18)
    out(f"Pooled SD of firm ROA = {roa_sd:.2f} pts -> minimum detectable ROA gap = {d80 * roa_sd:.1f} pts")

    out("\n== Panel regressions: year fixed effects, SEs clustered by firm (20 clusters) ==")
    df["mode"] = pd.Categorical(df["mode"], ["Truck", "Rail", "Air"])
    specs = [
        ("M1 margin", "margin ~ C(mode) + C(year)", df),
        ("M1 margin, excluding 2020", "margin ~ C(mode) + C(year)", df[df.year != 2020]),
        ("M2 margin + capital intensity", "margin ~ C(mode) + log_ppe_rev + C(year)", df.dropna(subset=["log_ppe_rev"])),
        ("M3 return on assets", "roa ~ C(mode) + C(year)", df.dropna(subset=["roa"])),
        ("M4 capital intensity only", "margin ~ log_ppe_rev + C(year)", df.dropna(subset=["log_ppe_rev"])),
    ]
    for name, f, d in specs:
        m = clustered(f, d)
        out(f"\n{name}: n = {int(m.nobs)}, R2 = {m.rsquared:.3f}")
        out(coef_table(m).to_string())
    full = panel.copy()
    full["mode"] = pd.Categorical(full["mode"], ["Truck", "Rail", "Air"])
    m = clustered("margin ~ C(mode) + C(year)", full)
    out(f"\nRobustness, fiscal 2007-2025 (n = {int(m.nobs)}): rail coefficient = {m.params['C(mode)[T.Rail]']:.2f} (SE {m.bse['C(mode)[T.Rail]']:.2f})")

    m = smf.ols("margin ~ C(mode) + C(year)", df).fit()
    out(f"\nM1 residual Shapiro-Wilk W = {st.shapiro(m.resid).statistic:.3f}, p = {st.shapiro(m.resid).pvalue:.3g}")
    out(f"M1 Breusch-Pagan LM = {het_breuschpagan(m.resid, m.model.exog)[0]:.1f}, p = {het_breuschpagan(m.resid, m.model.exog)[1]:.3g}")

    x = fm.dropna(subset=["ppe_rev"])
    r = st.pearsonr(np.log(x.ppe_rev), x.margin)
    rho = st.spearmanr(x.ppe_rev, x.margin)
    out(f"\nFirm level: r(margin, log PP&E/revenue) = {r.statistic:.2f}, p = {r.pvalue:.3g}; Spearman rho = {rho.statistic:.2f}, p = {rho.pvalue:.3f}")

    out("\n== Price indexes ==")
    prices = pd.DataFrame({"rail": fred("PCU482111482111"), "truck": fred("PCU484121484121"),
                           "air": fred("CUSR0000SETG01"), "cpi": fred("CPIAUCSL")}).loc[:2025]
    prices["real_rail"] = prices.rail / prices.cpi
    prices["real_rail"] = prices.real_rail / prices.real_rail[1980] * 100
    prices["real_air"] = prices.air / prices.cpi
    prices["real_air"] = prices.real_air / prices.real_air[1989] * 100
    prices.to_csv(PROCESSED / "prices_annual.csv", index_label="year")
    rr = prices.real_rail
    out("Real rail rate (1980 = 100):", rr.loc[[1969, 1980, 1981, 2001, 2025]].round(1).to_dict())
    out(f"Change 1981-2001: {(rr[2001] / rr[1981] - 1) * 100:.1f}%; 2001-2025: {(rr[2025] / rr[2001] - 1) * 100:.1f}%")
    out("Real airfare (1989 = 100), 2025:", round(prices.real_air[2025], 1))
    b = prices.loc[2004:2025]
    for c in ["rail", "truck", "air", "cpi"]:
        out(f"{c:5s} 2004-2025: {(b[c].iloc[-1] / b[c].iloc[0] - 1) * 100:.1f}%")
    ch = prices[["rail", "truck", "air", "cpi"]].pct_change().loc[2005:2025] * 100
    out("Years with a price decline, 2005-2025:", (ch < 0).sum().to_dict())
    out(f"Levene test on annual % changes (rail, truck, air): p = {st.levene(ch.rail, ch.truck, ch.air).pvalue:.3f}")
    out.save()


if __name__ == "__main__":
    main()
