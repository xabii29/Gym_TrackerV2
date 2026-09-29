-- 00: esquema v2 de Gym Tracker. Idempotente (se puede ejecutar varias veces).
BEGIN;

-- Si ya existe una tabla con el mismo nombre pero de otra versión/estructura, se RENOMBRA a <nombre>_previo
-- (no se borra nada) para que el esquema v2 se cree limpio.
DO $$
DECLARE
    t RECORD;
    cols_ok BOOLEAN;
    ident_ok BOOLEAN;
BEGIN
    FOR t IN SELECT * FROM (VALUES
        ('ejercicios',          ARRAY['id','nombre','nombre_en','categoria','musculo_objetivo','activo','revisar'], FALSE),
        ('ejercicios_alias',    ARRAY['alias','ejercicio_id'], FALSE),
        ('sesiones',            ARRAY['id','fecha','inicio','fin','plantilla','notas','estado'], TRUE),
        ('series',              ARRAY['id','sesion_id','ejercicio_id','orden','serie','reps','peso_kg','es_calentamiento'], TRUE),
        ('plantillas',          ARRAY['id','nombre'], TRUE),
        ('plantilla_ejercicios',ARRAY['plantilla_id','orden','ejercicio_id'], FALSE),
        ('ajustes',             ARRAY['clave','valor'], FALSE),
        ('peso_corporal',       ARRAY['fecha','peso_kg'], FALSE),
        ('_migraciones',        ARRAY['nombre','aplicado_en'], FALSE)
    ) AS x(tabla, columnas, con_identidad)
    LOOP
        IF to_regclass('public.' || t.tabla) IS NULL THEN CONTINUE; END IF;
        SELECT COUNT(*) = array_length(t.columnas, 1) INTO cols_ok
          FROM information_schema.columns
         WHERE table_schema = 'public' AND table_name = t.tabla AND column_name = ANY (t.columnas);
        ident_ok := TRUE;
        IF t.con_identidad THEN
            SELECT EXISTS (SELECT 1 FROM pg_attribute
                            WHERE attrelid = ('public.' || t.tabla)::regclass AND attname = 'id'
                              AND attidentity <> '') INTO ident_ok;
        END IF;
        IF NOT (cols_ok AND ident_ok) THEN
            EXECUTE format('DROP TABLE IF EXISTS public.%I CASCADE', t.tabla || '_previo');
            EXECUTE format('ALTER TABLE public.%I RENAME TO %I', t.tabla, t.tabla || '_previo');
            RAISE NOTICE 'La tabla % tenía otra estructura: se renombró a %_previo (sus datos siguen ahí).', t.tabla, t.tabla;
        END IF;
    END LOOP;
END $$;

CREATE TABLE IF NOT EXISTS ejercicios (
    id                   TEXT PRIMARY KEY,
    nombre               TEXT NOT NULL,
    nombre_en            TEXT,
    categoria            TEXT NOT NULL,
    musculo_objetivo     TEXT NOT NULL,
    musculos_secundarios TEXT[],
    equipo               TEXT,
    instrucciones_es     TEXT,
    personalizado        BOOLEAN NOT NULL DEFAULT FALSE,
    activo               BOOLEAN NOT NULL DEFAULT TRUE,
    revisar              BOOLEAN NOT NULL DEFAULT FALSE   -- nombre pendiente de revisión manual
);
CREATE UNIQUE INDEX IF NOT EXISTS ux_ejercicios_nombre ON ejercicios (lower(nombre));
CREATE INDEX IF NOT EXISTS ix_ejercicios_filtro ON ejercicios (categoria, musculo_objetivo) WHERE activo;

-- nombres antiguos (v1) -> id, para migrar registros y plantillas
CREATE TABLE IF NOT EXISTS ejercicios_alias (
    alias        TEXT PRIMARY KEY,
    ejercicio_id TEXT NOT NULL REFERENCES ejercicios(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS sesiones (
    id        BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    fecha     DATE NOT NULL DEFAULT (now() AT TIME ZONE 'America/Mexico_City')::date,
    inicio    TIMESTAMPTZ NOT NULL DEFAULT now(),
    fin       TIMESTAMPTZ,
    plantilla TEXT,
    notas     TEXT NULL,
    estado    TEXT NOT NULL DEFAULT 'en_curso' CHECK (estado IN ('en_curso', 'terminada')),
    CHECK (fin IS NULL OR fin >= inicio)
);
CREATE INDEX IF NOT EXISTS ix_sesiones_fecha ON sesiones (fecha DESC);
-- solo puede haber una sesión abierta a la vez
CREATE UNIQUE INDEX IF NOT EXISTS ux_sesion_en_curso ON sesiones (estado) WHERE estado = 'en_curso';

CREATE TABLE IF NOT EXISTS series (
    id               BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    sesion_id        BIGINT NOT NULL REFERENCES sesiones(id) ON DELETE CASCADE,
    ejercicio_id     TEXT NOT NULL REFERENCES ejercicios(id),
    orden            SMALLINT NOT NULL,
    serie            SMALLINT NOT NULL,
    reps             SMALLINT NOT NULL CHECK (reps >= 0),
    peso_kg          NUMERIC(6,2) NOT NULL DEFAULT 0 CHECK (peso_kg >= 0),
    rpe              NUMERIC(3,1) CHECK (rpe BETWEEN 1 AND 10),
    es_calentamiento BOOLEAN NOT NULL DEFAULT FALSE,
    nota             TEXT NULL,
    UNIQUE (sesion_id, ejercicio_id, serie)
);
CREATE INDEX IF NOT EXISTS ix_series_ejercicio ON series (ejercicio_id, sesion_id);
CREATE INDEX IF NOT EXISTS ix_series_sesion ON series (sesion_id, orden);

CREATE TABLE IF NOT EXISTS plantillas (
    id     BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nombre TEXT NOT NULL UNIQUE
);
CREATE TABLE IF NOT EXISTS plantilla_ejercicios (
    plantilla_id BIGINT NOT NULL REFERENCES plantillas(id) ON DELETE CASCADE,
    orden        SMALLINT NOT NULL,
    ejercicio_id TEXT NOT NULL REFERENCES ejercicios(id),
    PRIMARY KEY (plantilla_id, orden)
);

CREATE TABLE IF NOT EXISTS ajustes (clave TEXT PRIMARY KEY, valor JSONB NOT NULL);
CREATE TABLE IF NOT EXISTS peso_corporal (
    fecha   DATE PRIMARY KEY,
    peso_kg NUMERIC(5,2) NOT NULL CHECK (peso_kg > 0)
);
CREATE TABLE IF NOT EXISTS _migraciones (
    nombre      TEXT PRIMARY KEY,
    aplicado_en TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ------------------------------------------------------------------ vistas
CREATE OR REPLACE VIEW v_series_detalle AS
SELECT se.fecha, se.id AS sesion_id, sr.orden, sr.ejercicio_id, e.nombre AS ejercicio,
       e.categoria, e.musculo_objetivo, sr.serie, sr.peso_kg, sr.reps, sr.rpe,
       (sr.peso_kg * sr.reps) AS volumen_kg,
       CASE WHEN sr.reps = 1 THEN sr.peso_kg
            ELSE ROUND(sr.peso_kg * (1 + sr.reps / 30.0), 1) END AS e1rm_kg
FROM series sr
JOIN sesiones se ON se.id = sr.sesion_id
JOIN ejercicios e ON e.id = sr.ejercicio_id
WHERE NOT sr.es_calentamiento;

CREATE OR REPLACE VIEW v_prs AS
SELECT DISTINCT ON (ejercicio_id)
       ejercicio_id, ejercicio, categoria, musculo_objetivo, peso_kg, reps, e1rm_kg, fecha
FROM v_series_detalle
ORDER BY ejercicio_id, peso_kg DESC, reps DESC, fecha ASC;

CREATE OR REPLACE VIEW v_pr_historial AS
SELECT fecha, ejercicio_id, ejercicio, peso_kg, reps, e1rm_kg
FROM (
    SELECT fecha, ejercicio_id, ejercicio, peso_kg, reps, e1rm_kg,
           MAX(peso_kg) OVER (PARTITION BY ejercicio_id
                              ORDER BY fecha, sesion_id, serie
                              ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING) AS previo
    FROM v_series_detalle
) t
WHERE previo IS NULL OR peso_kg > previo;

CREATE OR REPLACE VIEW v_sesiones_resumen AS
SELECT s.id, s.fecha, s.inicio, s.fin, s.plantilla, s.notas, s.estado,
       COUNT(DISTINCT sr.ejercicio_id) AS n_ejercicios,
       COUNT(sr.id) FILTER (WHERE NOT sr.es_calentamiento) AS n_series,
       COALESCE(SUM(sr.peso_kg * sr.reps) FILTER (WHERE NOT sr.es_calentamiento), 0) AS volumen_kg,
       ROUND(EXTRACT(EPOCH FROM (s.fin - s.inicio)) / 60) AS duracion_min
FROM sesiones s
LEFT JOIN series sr ON sr.sesion_id = s.id
GROUP BY s.id;


-- --------------------------------------------- función: guardar un ejercicio en UN viaje
CREATE OR REPLACE FUNCTION guardar_ejercicio_sesion(
    p_sesion BIGINT, p_ejercicio TEXT, p_reps INT[], p_pesos NUMERIC[], p_cals BOOLEAN[],
    p_rpe NUMERIC, p_nota TEXT
) RETURNS VOID LANGUAGE plpgsql AS $fn$
DECLARE v_orden SMALLINT;
BEGIN
    SELECT orden INTO v_orden FROM series WHERE sesion_id = p_sesion AND ejercicio_id = p_ejercicio LIMIT 1;
    IF v_orden IS NULL THEN
        SELECT COALESCE(MAX(orden), 0) + 1 INTO v_orden FROM series WHERE sesion_id = p_sesion;
    END IF;
    DELETE FROM series WHERE sesion_id = p_sesion AND ejercicio_id = p_ejercicio;
    IF COALESCE(array_length(p_reps, 1), 0) = 0 THEN RETURN; END IF;
    INSERT INTO series (sesion_id, ejercicio_id, orden, serie, reps, peso_kg, es_calentamiento, rpe, nota)
    SELECT p_sesion, p_ejercicio, v_orden, u.n::smallint, u.reps, u.peso, u.cal, p_rpe,
           CASE WHEN u.n = 1 THEN p_nota END
    FROM unnest(p_reps, p_pesos, p_cals) WITH ORDINALITY AS u(reps, peso, cal, n);
END $fn$;
REVOKE ALL ON FUNCTION guardar_ejercicio_sesion(BIGINT, TEXT, INT[], NUMERIC[], BOOLEAN[], NUMERIC, TEXT) FROM PUBLIC;

-- ------------------------------------------- seguridad (Supabase / Data API)
DO $$
DECLARE t TEXT;
BEGIN
    FOREACH t IN ARRAY ARRAY['ejercicios','ejercicios_alias','sesiones','series','plantillas',
                             'plantilla_ejercicios','ajustes','peso_corporal','_migraciones']
    LOOP
        EXECUTE format('ALTER TABLE %I ENABLE ROW LEVEL SECURITY', t);
    END LOOP;
    -- las vistas respetan los permisos de quien consulta (PG15+)
    IF current_setting('server_version_num')::int >= 150000 THEN
        EXECUTE 'ALTER VIEW v_series_detalle SET (security_invoker = on)';
        EXECUTE 'ALTER VIEW v_prs SET (security_invoker = on)';
        EXECUTE 'ALTER VIEW v_pr_historial SET (security_invoker = on)';
        EXECUTE 'ALTER VIEW v_sesiones_resumen SET (security_invoker = on)';
    END IF;
    -- roles públicos de Supabase: sin acceso (la app entra con el usuario postgres)
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'anon') THEN
        EXECUTE 'REVOKE ALL ON ALL TABLES IN SCHEMA public FROM anon';
    END IF;
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'authenticated') THEN
        EXECUTE 'REVOKE ALL ON ALL TABLES IN SCHEMA public FROM authenticated';
    END IF;
END $$;

COMMIT;
