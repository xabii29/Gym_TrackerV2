-- 04 (OPCIONAL): migra la tabla antigua `registros` (v1) al esquema v2.
-- Ejecutar DESPUÉS de 00..03. Si no existe `registros`, no hace nada.
-- Agrupa en una sesión todas las filas con la misma `fecha` exacta (mismo NOW() de la subida).
-- NO borra `registros`: queda como respaldo. Es re-ejecutable (no duplica).
DO $$
DECLARE
    tiene_notas BOOLEAN;
    n_sesiones  INT;
BEGIN
    PERFORM set_config('TimeZone', 'UTC', true);   -- interpretación determinista de fecha::timestamptz
    IF to_regclass('public.registros') IS NULL THEN
        RAISE NOTICE 'No existe la tabla registros: nada que migrar.';
        RETURN;
    END IF;
    IF EXISTS (SELECT 1 FROM _migraciones WHERE nombre = '04_migrar_registros_v1') THEN
        RAISE NOTICE 'Ya se migró antes.';
        RETURN;
    END IF;

    SELECT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name = 'registros' AND column_name = 'notas_sesion') INTO tiene_notas;

    -- 1) ejercicios que no están en el catálogo -> personalizados (no se pierde nada)
    INSERT INTO ejercicios (id, nombre, categoria, musculo_objetivo, personalizado)
    SELECT 'custom-' || substr(md5(lower(trim(r.ejercicio))), 1, 10),
           trim(r.ejercicio), 'sin_clasificar', 'sin_clasificar', TRUE
    FROM (SELECT DISTINCT ejercicio FROM registros WHERE ejercicio IS NOT NULL) r
    WHERE NOT EXISTS (SELECT 1 FROM ejercicios_alias a WHERE a.alias = lower(trim(r.ejercicio)))
      AND NOT EXISTS (SELECT 1 FROM ejercicios e WHERE lower(e.nombre) = lower(trim(r.ejercicio)))
    ON CONFLICT DO NOTHING;

    -- 2) tabla temporal con el id resuelto y el orden físico de inserción
    CREATE TEMP TABLE _reg ON COMMIT DROP AS
    SELECT r.fecha::timestamptz AS ts,
           COALESCE(a.ejercicio_id, e.id,
                    'custom-' || substr(md5(lower(trim(r.ejercicio))), 1, 10)) AS ejercicio_id,
           r.serie::int AS serie, r.reps::int AS reps, COALESCE(r.peso_kg, 0) AS peso_kg,
           row_number() OVER (ORDER BY r.ctid) AS rn
    FROM registros r
    LEFT JOIN ejercicios_alias a ON a.alias = lower(trim(r.ejercicio))
    LEFT JOIN ejercicios e ON lower(e.nombre) = lower(trim(r.ejercicio));

    -- 3) una sesión por cada fecha exacta (terminada)
    CREATE TEMP TABLE _ses ON COMMIT DROP AS
    SELECT ts, MIN(rn) AS primero,
           -- fecha sin hora (00:00 exacta) = fecha de calendario tal cual; con hora = instante -> día local
           CASE WHEN (ts AT TIME ZONE 'UTC')::time = TIME '00:00' THEN (ts AT TIME ZONE 'UTC')::date
                ELSE (ts AT TIME ZONE 'America/Mexico_City')::date END AS fecha_local
    FROM _reg GROUP BY ts;

    CREATE TEMP TABLE _map (ts timestamptz, sesion_id bigint) ON COMMIT DROP;
    WITH ins AS (
        INSERT INTO sesiones (fecha, inicio, fin, estado)
        SELECT fecha_local, ts, ts, 'terminada' FROM _ses ORDER BY ts
        RETURNING id, inicio
    )
    INSERT INTO _map SELECT inicio, id FROM ins;
    GET DIAGNOSTICS n_sesiones = ROW_COUNT;

    IF tiene_notas THEN
        EXECUTE $q$
            UPDATE sesiones s SET notas = n.nota
            FROM (SELECT fecha::timestamptz AS ts, MAX(NULLIF(trim(notas_sesion), '')) AS nota
                  FROM registros GROUP BY fecha) n
            WHERE s.inicio = n.ts AND n.nota IS NOT NULL
        $q$;
    END IF;

    -- 4) series: orden del ejercicio = primera aparición en la sesión
    INSERT INTO series (sesion_id, ejercicio_id, orden, serie, reps, peso_kg)
    SELECT m.sesion_id, x.ejercicio_id,
           DENSE_RANK() OVER (PARTITION BY m.sesion_id ORDER BY x.primera)::smallint,
           x.serie, x.reps, x.peso_kg
    FROM (SELECT ts, ejercicio_id, serie, reps, peso_kg, rn,
                 MIN(rn) OVER (PARTITION BY ts, ejercicio_id) AS primera,
                 ROW_NUMBER() OVER (PARTITION BY ts, ejercicio_id, serie ORDER BY rn) AS dup
          FROM _reg) x
    JOIN _map m ON m.ts = x.ts
    WHERE x.dup = 1
    ON CONFLICT DO NOTHING;

    INSERT INTO _migraciones (nombre) VALUES ('04_migrar_registros_v1');
    RAISE NOTICE 'Migradas % sesiones.', n_sesiones;
END $$;

-- Cuando confirmes que todo se ve bien en la app, puedes archivar la tabla antigua:
--   ALTER TABLE registros RENAME TO registros_v1_respaldo;
