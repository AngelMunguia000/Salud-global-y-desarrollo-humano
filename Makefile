.PHONY: etl test all

PYTHON ?= python

etl:
	$(PYTHON) -m etl.pipeline

test: etl
	$(PYTHON) -m pytest -q

all: test
