.PHONY: test figures
test:
	python -m pytest -q
figures:
	python scripts/experiments.py && python scripts/field_demo.py && python scripts/make_figures.py && python scripts/make_facts.py
