-- Drop old VARCHAR role column (attnum=4)
ALTER TABLE users DROP COLUMN IF EXISTS role;
-- Verify and check
SELECT column_name, data_type, attnum, attnotnull, adbin IS NOT NULL AS has_default
FROM pg_attribute
JOIN pg_class ON pg_class.oid = pg_attribute.attrelid
LEFT JOIN pg_attrdef ON pg_attrdef.adrelid = pg_class.oid AND pg_attrdef.adnum = pg_attribute.attnum
JOIN information_schema.columns c ON c.table_name = pg_class.relname AND c.column_name = pg_attribute.attname AND c.table_schema = 'public'
WHERE pg_class.relname = 'users' AND pg_attribute.attname = 'role' AND pg_attribute.attnum > 0
ORDER BY pg_attribute.attnum;
