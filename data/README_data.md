# Organización de los datos

- `00_raw/`: copias originales sin modificación.
- `01_processed/`: datos con transformaciones iniciales.
- `02_clean/`: datos depurados y validados.
- `03_consolidated/`: conjunto integrado por país y año.

No sobrescribir archivos originales. Registrar fuente, fecha de descarga, transformaciones, unidades y limitaciones. Revisar el tamaño de los archivos y las reglas del repositorio antes de versionar datasets grandes; los archivos pueden documentarse o gestionarse aparte si fuera necesario.
