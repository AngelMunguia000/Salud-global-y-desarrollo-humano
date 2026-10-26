.PHONY: etl test all

PYTHON ?= python

etl:
	$(PYTHON) -m 02_ingenieria.etl.pipeline

test: etl
	$(PYTHON) -m pytest -q

all: test
