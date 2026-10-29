-- Consultas de ejemplo sobre warehouse/salud.db (DuckDB). Contrato §5.8 / criterio A6.
-- Esquema: dim_pais(iso3, pais, region)
--          dim_indicador(codigo_indicador, nombre, unidad)
--          hechos_indicador(iso3, anio, codigo_indicador, valor)

-- Q1. Esperanza de vida de México, últimos 5 años disponibles
SELECT h.anio, ROUND(h.valor, 1) AS esperanza_vida
FROM hechos_indicador h
WHERE h.iso3 = 'MEX' AND h.codigo_indicador = 'SP.DYN.LE00.IN'
ORDER BY h.anio DESC
LIMIT 5;

-- Q2. Top 10 países por esperanza de vida en 2023
SELECT p.pais, p.region, ROUND(h.valor, 1) AS esperanza_vida
FROM hechos_indicador h JOIN dim_pais p USING (iso3)
WHERE h.codigo_indicador = 'SP.DYN.LE00.IN' AND h.anio = 2023
ORDER BY h.valor DESC
LIMIT 10;

-- Q3. Esperanza de vida media por región en años clave
SELECT p.region, h.anio, ROUND(AVG(h.valor), 1) AS esperanza_vida_media
FROM hechos_indicador h JOIN dim_pais p USING (iso3)
WHERE h.codigo_indicador = 'SP.DYN.LE00.IN' AND h.anio IN (1960, 1990, 2023)
GROUP BY p.region, h.anio
ORDER BY p.region, h.anio;

-- Q4. Cobertura (n.º de países con dato) por indicador y año seleccionado
SELECT i.nombre, h.anio, COUNT(DISTINCT h.iso3) AS paises_con_dato
FROM hechos_indicador h JOIN dim_indicador i USING (codigo_indicador)
WHERE h.anio IN (2000, 2010, 2023)
GROUP BY i.nombre, h.anio
ORDER BY i.nombre, h.anio;

-- Q5. Panel ancho 2021 (esperanza de vida, PIB per cápita, gasto en salud per cápita)
SELECT p.pais,
       MAX(CASE WHEN h.codigo_indicador = 'SP.DYN.LE00.IN'     THEN h.valor END) AS esperanza_vida,
       MAX(CASE WHEN h.codigo_indicador = 'NY.GDP.PCAP.PP.KD'  THEN h.valor END) AS pib_pc_ppa,
       MAX(CASE WHEN h.codigo_indicador = 'SH.XPD.CHEX.PP.CD'  THEN h.valor END) AS gasto_salud_pc
FROM hechos_indicador h JOIN dim_pais p USING (iso3)
WHERE h.anio = 2021
GROUP BY p.pais
HAVING COUNT(*) >= 3
ORDER BY esperanza_vida DESC
LIMIT 15;

-- Q6. Países con esperanza de vida >= 75 y PIB per cápita < 15,000 (2021)
SELECT p.pais, ROUND(le.valor, 1) AS esperanza_vida, ROUND(pib.valor, 0) AS pib_pc_ppa
FROM hechos_indicador le
JOIN hechos_indicador pib ON pib.iso3 = le.iso3 AND pib.anio = le.anio
JOIN dim_pais p ON p.iso3 = le.iso3
WHERE le.codigo_indicador = 'SP.DYN.LE00.IN' AND pib.codigo_indicador = 'NY.GDP.PCAP.PP.KD'
  AND le.anio = 2021 AND le.valor >= 75 AND pib.valor < 15000
ORDER BY le.valor DESC;
