.PHONY: test lint build estimate identify scenarios dashboard

PYTHON ?= python3

test:
	$(PYTHON) -m pytest

lint:
	$(PYTHON) -m ruff check src tests

build:
	$(PYTHON) -m pricing_research.data.build

estimate:
	$(PYTHON) -m pricing_research.estimation.run

identify:
	$(PYTHON) -m pricing_research.estimation.identify

scenarios:
	$(PYTHON) -m pricing_research.economics.counterfactual

dashboard:
	$(PYTHON) -m streamlit run src/pricing_research/dashboard/app.py
