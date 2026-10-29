# Pipeline reproducible — Salud global y desarrollo humano (Equipo 4)
# Uso: `make help`. Ejecutar siempre desde la raíz del repositorio.
.PHONY: help install etl analisis modelos informe consultas test app all clean-resultados

PYTHON ?= python

help:  ## Lista los comandos disponibles
	@grep -E '^[a-z-]+:.*##' $(MAKEFILE_LIST) | awk -F':.*## ' '{printf "  make %-18s %s\n", $$1, $$2}'

install:  ## Instala dependencias
	$(PYTHON) -m pip install -r requirements.txt

etl:  ## Ingeniería: extrae, transforma, integra y carga (panel + almacén)
	$(PYTHON) -m 02_ingenieria.etl.pipeline

analisis:  ## Análisis exploratorio: tablas y figuras (04_analisis)
	$(PYTHON) -m 04_analisis.scripts.eda_completo

modelos: analisis  ## Ciencia de datos: modelos M0–M6, residuos, hipótesis (05_ciencia)
	$(PYTHON) -m 05_ciencia.scripts.modelos

informe: modelos  ## Informe final (.md/.docx) y presentación (.pptx) en reports/
	$(PYTHON) -m reports.generar_informe

consultas:  ## Ejecuta las consultas SQL de ejemplo sobre warehouse/salud.db
	$(PYTHON) -m 02_ingenieria.etl.consultas

test: etl  ## Pruebas de calidad de datos, estadística y entregables
	$(PYTHON) -m pytest -q

app:  ## Aplicación web de Streamlit en http://localhost:8501 (06_despliegue)
	$(PYTHON) -m streamlit run 06_despliegue/app.py

all: etl analisis modelos informe test  ## Todo el proyecto, de datos originales a informe

clean-resultados:  ## Borra resultados generados (no toca datos originales)
	rm -f 04_analisis/tablas/* 04_analisis/visualizaciones/* 05_ciencia/resultados/* 05_ciencia/figuras/* \
	      reports/informe_final.* reports/presentacion_final.pptx reports/figuras/*
