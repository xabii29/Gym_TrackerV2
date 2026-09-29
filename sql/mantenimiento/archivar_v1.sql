-- Mueve las tablas de la versión anterior al esquema `archivo_v1` (fuera de `public`).
-- NO borra nada: los datos siguen ahí, pero dejan de estorbar y la API pública de Supabase no los expone.
-- Se archivan: registros (solo si ya está migrada o vacía), series_registradas y todas las *_previo.
-- Cuando estés seguro de que no las necesitas:   DROP SCHEMA archivo_v1 CASCADE;
-- Para deshacer una tabla:                        ALTER TABLE archivo_v1.registros SET SCHEMA public;
BEGIN;
CREATE SCHEMA IF NOT EXISTS archivo_v1;
REVOKE ALL ON SCHEMA archivo_v1 FROM PUBLIC;

DO $$
DECLARE
    t RECORD;
    n BIGINT;
BEGIN
    IF to_regclass('public.registros') IS NOT NULL AND to_regclass('archivo_v1.registros') IS NULL THEN
        EXECUTE 'SELECT count(*) FROM public.registros' INTO n;
        IF n = 0 OR EXISTS (SELECT 1 FROM _migraciones WHERE nombre = '04_migrar_registros_v1') THEN
            ALTER TABLE public.registros SET SCHEMA archivo_v1;
            RAISE NOTICE 'registros archivada (% filas).', n;
        ELSE
            RAISE NOTICE 'registros NO se archivó: tiene % filas y aún no se migra (python scripts/instalar_bd.py --migrar-v1).', n;
        END IF;
    END IF;

    FOR t IN SELECT tablename FROM pg_tables
              WHERE schemaname = 'public'
                AND (tablename LIKE E'%\\_previo' OR tablename = 'series_registradas')
    LOOP
        IF to_regclass('archivo_v1.' || quote_ident(t.tablename)) IS NULL THEN
            EXECUTE format('ALTER TABLE public.%I SET SCHEMA archivo_v1', t.tablename);
            RAISE NOTICE 'archivada: %', t.tablename;
        ELSE
            RAISE NOTICE 'ya existe archivo_v1.% : se omite', t.tablename;
        END IF;
    END LOOP;
END $$;
COMMIT;

-- Comprobación:  SELECT table_schema, table_name FROM information_schema.tables
--                WHERE table_schema IN ('public','archivo_v1') ORDER BY 1, 2;
