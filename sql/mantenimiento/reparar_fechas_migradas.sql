-- Repara sesiones YA migradas desde `registros` cuya fecha quedó un día antes de lo real.
-- Causa: la tabla v1 guardaba solo la fecha (00:00 UTC) y se convirtió a hora de México (día anterior, 18:00).
-- Solo toca sesiones migradas (fin = inicio) con hora exacta 00:00 UTC. Seguro de re-ejecutar.
UPDATE sesiones
   SET fecha = (inicio AT TIME ZONE 'UTC')::date
 WHERE estado = 'terminada'
   AND fin = inicio
   AND (inicio AT TIME ZONE 'UTC')::time = TIME '00:00'
   AND fecha <> (inicio AT TIME ZONE 'UTC')::date;

-- Verifica:  SELECT id, fecha, inicio FROM sesiones ORDER BY id;
