# Data

All inputs are public and free to download. `make fetch` re-creates `data/raw/` from the original sources.

## Raw

| Folder | Source | Notes |
|---|---|---|
| `raw/fred/` | [FRED](https://fred.stlouisfed.org/), Federal Reserve Bank of St. Louis | One CSV per series. Committed to the repo (180 KB). Series IDs and descriptions are in `src/config.py`. The historical railroad series come from the [NBER Macrohistory Database](https://www.nber.org/research/data/nber-macrohistory-database). |
| `raw/sec/` | [SEC EDGAR XBRL company facts API](https://www.sec.gov/edgar/sec-api-documentation) | One JSON file per company, named by CIK. Not committed (about 60 MB). Set `SEC_USER_AGENT` before running `make fetch`, as the SEC asks automated clients to identify themselves. |

## Processed

| File | Unit of observation | Built by |
|---|---|---|
| `firm_panel.csv` | Firm-year, fiscal 2007–2025, 20 firms | `src/build_panel.py` |
| `firm_means.csv` | Firm, averages over fiscal 2009–2025 | `src/analysis_modern.py` |
| `prices_annual.csv` | Year, 1947–2025 | `src/analysis_modern.py` |
| `historical_rates.csv` | Year, 1865–1955 | `src/analysis_historical.py` |
| `historical_margins.csv` | Year, 1908–1961 | `src/analysis_historical.py` |

### `firm_panel.csv` columns

| Column | Definition |
|---|---|
| `cik` | SEC Central Index Key |
| `firm`, `mode` | Short company name; Rail, Truck or Air |
| `year` | Fiscal year (years ending January–June are assigned to the prior year) |
| `revenue`, `op_income` | Annual revenue and operating income, USD, from 10-K filings |
| `ppe`, `assets` | Net property, plant and equipment and total assets at fiscal year end, USD |
| `margin` | `op_income / revenue × 100` |
| `roa` | `op_income / assets × 100` |
| `ppe_rev`, `log_ppe_rev` | Net PP&E per dollar of revenue, and its natural log |
| `ppe_assets` | Net PP&E as a share of total assets |

### Construction notes

* **Revenue tags.** Filers moved between XBRL revenue tags over time (`Revenues`, `RevenueFromContractWithCustomer…`). The builder takes the first listed tag and lets a later tag replace it when that tag reports a larger figure for the same year. Restated values replace originals.
* **Sample edges.** Knight-Swift enters in 2017, the year of the merger. Schneider enters at its 2017 IPO with comparatives from 2015. Kansas City Southern leaves after 2022, when it was acquired. BNSF has no usable 2010 figure because of its 2010 acquisition by Berkshire Hathaway.
* **Freight-rate splice.** `historical_rates.csv` joins four NBER series with different railroad coverage: thirteen railroads to 1881 (rescaled to the all-railroads level using the 1882–1890 overlap), all railroads 1882–1919, and Class I railroads 1920–1955. The deflator is the NBER general price level to 1912, chained to the CPI from 1913 using the 1913–1920 overlap.
* **Historical margins.** Monthly Class I revenue and expenses summed by calendar year. Only years with all twelve months are kept.
