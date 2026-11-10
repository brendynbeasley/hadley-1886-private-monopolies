PY ?= python3

.PHONY: all fetch panel analysis figures report clean

all: panel analysis figures report

fetch:          ## download FRED and SEC data (needs SEC_USER_AGENT)
	cd src && $(PY) fetch_data.py

panel:          ## build data/processed/firm_panel.csv from SEC filings
	cd src && $(PY) build_panel.py

analysis:       ## run both analyses, write results/*.txt
	cd src && $(PY) analysis_modern.py && $(PY) analysis_historical.py

figures:        ## write figures/*.svg
	cd src && $(PY) make_figures.py

report:         ## write docs/index.html
	cd src && $(PY) build_report.py

clean:
	rm -rf data/processed/* results/* figures/* docs/index.html
