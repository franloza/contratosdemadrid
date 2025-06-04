CREATE OR REPLACE TABLE contracts.main.refined_contracts AS
WITH
-- Step 1: Select raw columns and identifiers needed for ordering and grouping
raw_with_ids AS (
    SELECT
        filename,
        row_number, -- Crucial for ordering
        "Tipo de Publicación" AS tipo_de_publicacion_raw,
        "Estado" AS estado_raw,
        "Entidad Adjudicadora" AS entidad_adjudicadora_raw,
        "Nº Expediente" AS no_expediente_raw,
        "Referencia" AS referencia_raw,
        "Título del contrato" AS titulo_del_contrato_raw, -- Key indicator for a new contract
        "Tipo de contrato" AS tipo_de_contrato_raw,
        "Procedimiento de adjudicación" AS procedimiento_de_adjudicacion_raw,
        "Presupuesto de licitación" AS presupuesto_de_licitacion_raw,
        "Nº de ofertas" AS no_de_ofertas_raw,
        "Resultado" AS resultado_raw,
        "NIF del adjudicatario" AS nif_del_adjudicatario_raw,
        "Adjudicatario" AS adjudicatario_raw,
        "Fecha del contrato" AS fecha_del_contrato_raw,
        "Importe de adjudicación" AS importe_de_adjudicacion_raw,
        "Importe de las modificaciones" AS importe_de_las_modificaciones_raw,
        "Importe de las prórrogas" AS importe_de_las_prorrogas_raw,
        "Importe de la liquidación" AS importe_de_la_liquidacion_raw
    FROM contracts.main.raw_contracts
),
-- Step 2: Apply parsing and type casting (logic similar to refined_contracts)
parsed_and_typed AS (
    SELECT
        filename,
        row_number,
        titulo_del_contrato_raw, -- Retain for grouping logic

        -- Columns that might be forward-filled (pre-fill versions)
        tipo_de_publicacion_raw AS tipo_de_publicacion_pre_ffill,
        estado_raw AS estado_pre_ffill,
        split_part(entidad_adjudicadora_raw, '··>', 1) as adjudicador_raiz_pre_ffill,
        COALESCE(
          NULLIF(SPLIT_PART(entidad_adjudicadora_raw, '··>', 5),  ''),
          NULLIF(SPLIT_PART(entidad_adjudicadora_raw, '··>', 4),  ''),
          NULLIF(SPLIT_PART(entidad_adjudicadora_raw, '··>', 3),  ''),
          NULLIF(SPLIT_PART(entidad_adjudicadora_raw, '··>', 2),  ''),
          NULLIF(SPLIT_PART(entidad_adjudicadora_raw, '··>', 1),  '')
        ) AS adjudicador_pre_ffill,
        no_expediente_raw AS no_expediente_pre_ffill,
        referencia_raw AS referencia_pre_ffill,
        titulo_del_contrato_raw AS titulo_del_contrato_pre_ffill,
        COALESCE(
            NULLIF(
                TRIM(
                    CONCAT(
                        UPPER(LEFT(tipo_de_contrato_raw, 1)),
                        LOWER(SUBSTRING(tipo_de_contrato_raw, 2))
                    )
                ),
                ''
            ),
            'Desconocido'
        ) AS tipo_de_contrato_pre_ffill,
        procedimiento_de_adjudicacion_raw AS procedimiento_de_adjudicacion_pre_ffill,
        TRY_CAST(
            REPLACE(
                REPLACE(presupuesto_de_licitacion_raw, '.', ''),
                ',',
                '.'
            ) AS DOUBLE
        ) AS presupuesto_de_licitacion_pre_ffill,
        TRY_CAST(no_de_ofertas_raw AS BIGINT) AS no_de_ofertas_pre_ffill,
        resultado_raw AS resultado_pre_ffill,
        CAST(
            CASE
                WHEN regexp_matches(fecha_del_contrato_raw, '[0-9]{1,2} de [a-zA-Z]+ del [0-9]{4}') THEN
                    TRY_CAST(
                        regexp_extract(fecha_del_contrato_raw, '([0-9]{4})$', 1) || '-' ||
                        CASE LOWER(regexp_extract(fecha_del_contrato_raw, 'de ([a-zA-Z]+) del', 1))
                            WHEN 'enero' THEN '01' WHEN 'Enero' THEN '01'
                            WHEN 'febrero' THEN '02' WHEN 'Febrero' THEN '02'
                            WHEN 'marzo' THEN '03' WHEN 'Marzo' THEN '03'
                            WHEN 'abril' THEN '04' WHEN 'Abril' THEN '04'
                            WHEN 'mayo' THEN '05' WHEN 'Mayo' THEN '05'
                            WHEN 'junio' THEN '06' WHEN 'Junio' THEN '06'
                            WHEN 'julio' THEN '07' WHEN 'Julio' THEN '07'
                            WHEN 'agosto' THEN '08' WHEN 'Agosto' THEN '08'
                            WHEN 'septiembre' THEN '09' WHEN 'Septiembre' THEN '09'
                            WHEN 'octubre' THEN '10' WHEN 'Octubre' THEN '10'
                            WHEN 'noviembre' THEN '11' WHEN 'Noviembre' THEN '11'
                            WHEN 'diciembre' THEN '12' WHEN 'Diciembre' THEN '12'
                            ELSE NULL
                        END || '-' ||
                        LPAD(regexp_extract(fecha_del_contrato_raw, '^([0-9]{1,2})', 1), 2, '0')
                        AS DATE)
                ELSE NULL
            END
        AS DATE) AS fecha_del_contrato_pre_ffill,

        -- Columns specific to awardee (not forward-filled, but parsed)
        TRIM(REGEXP_REPLACE(UPPER(nif_del_adjudicatario_raw), '[^A-Z0-9]', '')) AS nif_del_adjudicatario,
        TRIM(REGEXP_REPLACE(REGEXP_REPLACE(UPPER(adjudicatario_raw), '\s+', ' '), ' 	', ' ')) AS adjudicatario,
        TRY_CAST(REPLACE(REPLACE(importe_de_adjudicacion_raw, '.', ''), ',', '.') AS DOUBLE) AS importe_de_adjudicacion,
        TRY_CAST(REPLACE(REPLACE(importe_de_las_modificaciones_raw, '.', ''), ',', '.') AS DOUBLE) AS importe_de_las_modificaciones,
        TRY_CAST(REPLACE(REPLACE(importe_de_las_prorrogas_raw, '.', ''), ',', '.') AS DOUBLE) AS importe_de_las_prorrogas,
        TRY_CAST(REPLACE(REPLACE(importe_de_la_liquidacion_raw, '.', ''), ',', '.') AS DOUBLE) AS importe_de_la_liquidacion
    FROM raw_with_ids
),
-- Step 3: Apply filter from refined_contracts and calculate importe_total
total_added AS (
    SELECT
        *,
        (COALESCE(importe_de_adjudicacion, 0) +
         COALESCE(importe_de_las_modificaciones, 0) +
         COALESCE(importe_de_las_prorrogas, 0) +
         COALESCE(importe_de_la_liquidacion, 0)) AS importe_total
    FROM parsed_and_typed
),
-- Step 4: Create a contract group identifier within each file
-- A new group starts when `titulo_del_contrato_pre_ffill` (which is the original title) is non-NULL.
grouped_for_ffill AS (
    SELECT
        *,
        SUM(CASE WHEN titulo_del_contrato_pre_ffill IS NOT NULL THEN 1 ELSE 0 END) OVER (PARTITION BY filename ORDER BY row_number ASC ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS contract_group_id
    FROM total_added
),
-- Step 5: Apply forward fill
forward_filled_data AS (
    SELECT
        -- Forward-filled columns (final versions)
        LAST_VALUE(tipo_de_publicacion_pre_ffill IGNORE NULLS) OVER (PARTITION BY filename, contract_group_id ORDER BY row_number ASC ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS tipo_de_publicacion,
        LAST_VALUE(estado_pre_ffill IGNORE NULLS) OVER (PARTITION BY filename, contract_group_id ORDER BY row_number ASC ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS estado,
        LAST_VALUE(adjudicador_raiz_pre_ffill IGNORE NULLS) OVER (PARTITION BY filename, contract_group_id ORDER BY row_number ASC ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS adjudicador_raiz,
        LAST_VALUE(adjudicador_pre_ffill IGNORE NULLS) OVER (PARTITION BY filename, contract_group_id ORDER BY row_number ASC ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS adjudicador,
        LAST_VALUE(no_expediente_pre_ffill IGNORE NULLS) OVER (PARTITION BY filename, contract_group_id ORDER BY row_number ASC ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS no_expediente,
        LAST_VALUE(referencia_pre_ffill IGNORE NULLS) OVER (PARTITION BY filename, contract_group_id ORDER BY row_number ASC ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS referencia,
        LAST_VALUE(titulo_del_contrato_pre_ffill IGNORE NULLS) OVER (PARTITION BY filename, contract_group_id ORDER BY row_number ASC ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS titulo_del_contrato,
        LAST_VALUE(tipo_de_contrato_pre_ffill IGNORE NULLS) OVER (PARTITION BY filename, contract_group_id ORDER BY row_number ASC ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS tipo_de_contrato,
        LAST_VALUE(procedimiento_de_adjudicacion_pre_ffill IGNORE NULLS) OVER (PARTITION BY filename, contract_group_id ORDER BY row_number ASC ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS procedimiento_de_adjudicacion,
        LAST_VALUE(presupuesto_de_licitacion_pre_ffill IGNORE NULLS) OVER (PARTITION BY filename, contract_group_id ORDER BY row_number ASC ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS presupuesto_de_licitacion,
        LAST_VALUE(no_de_ofertas_pre_ffill IGNORE NULLS) OVER (PARTITION BY filename, contract_group_id ORDER BY row_number ASC ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS no_de_ofertas,
        LAST_VALUE(resultado_pre_ffill IGNORE NULLS) OVER (PARTITION BY filename, contract_group_id ORDER BY row_number ASC ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS resultado,
        LAST_VALUE(fecha_del_contrato_pre_ffill IGNORE NULLS) OVER (PARTITION BY filename, contract_group_id ORDER BY row_number ASC ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS fecha_del_contrato,

        -- Columns not forward-filled (awardee specific)
        nif_del_adjudicatario,
        adjudicatario,
        importe_de_adjudicacion,
        importe_de_las_modificaciones,
        importe_de_las_prorrogas,
        importe_de_la_liquidacion,
        importe_total,
        
        -- Optionally, include these for verification, but they shouldn't be part of the final view's public interface
        filename,
        row_number,
        -- contract_group_id

    FROM grouped_for_ffill
),
-- Step 6: Add lote column
data_with_lote AS (
    SELECT
        * EXCLUDE (filename, row_number),
        row_number() OVER (PARTITION BY no_expediente, referencia, titulo_del_contrato ORDER BY filename, row_number) as lote
    FROM forward_filled_data
),
-- Step 8: Normalize contract types
normalized_contract_types AS (
    SELECT
        *,
        CASE 
            WHEN tipo_de_contrato = 'Suministro' THEN 'Suministros'
            WHEN tipo_de_contrato in ('servicios', 'Servicio', 'Concesión de servicios') THEN 'Servicios'
            WHEN tipo_de_contrato = 'Concesión de obras' THEN 'Obras'
            ELSE tipo_de_contrato
        END AS tipo_de_contrato_normalized
    FROM data_with_lote
)
-- Step 9: Add surrogate key and apply final filters
SELECT
    * EXCLUDE (tipo_de_contrato),
    tipo_de_contrato_normalized as tipo_de_contrato,
    md5(COALESCE(no_expediente, '') || '|' || COALESCE(referencia, '') || '|' || COALESCE(titulo_del_contrato, '') || '|' || COALESCE(nif_del_adjudicatario, '') || '|' || COALESCE(lote::VARCHAR, '')) AS contract_id
FROM normalized_contract_types

WHERE importe_total IS NOT NULL AND importe_total != 0 AND fecha_del_contrato IS NOT NULL
AND fecha_del_contrato >= '2021-01-01'
; 