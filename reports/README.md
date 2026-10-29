# Reportes y entregables

Esta carpeta reúne los resultados finales del proyecto, no los notebooks de trabajo.

Contenido previsto:
- Informe de resultados.
- Gráficos finales exportados.
- Tablas resumidas y documentadas.
- Conclusiones y limitaciones.
- Material para presentación.

Cada resultado debe indicar el periodo analizado, las fuentes, las unidades y las principales limitaciones.

## Estado y contenido (implementado)
- `informe_final.md` / `informe_final.docx`: informe con resumen ejecutivo, método, resultados (P1–P3), hipótesis, limitaciones y conclusiones.
- `presentacion_final.pptx`: 11 diapositivas.
- `figuras/`: gráficos finales usados en el informe.
- Se generan con `make informe` (`generar_informe.py`), que lee las cifras de `04_analisis/tablas` y `05_ciencia/resultados`.
