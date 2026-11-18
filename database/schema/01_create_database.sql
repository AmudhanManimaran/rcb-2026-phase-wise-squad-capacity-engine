-- =====================================================================
-- EeSaala Tracker | 01_create_database.sql
-- Run while connected to the default "postgres" database (pgAdmin Query
-- Tool or psql). The Python loader runs this automatically.
-- =====================================================================

-- psql:  \i database/schema/01_create_database.sql
-- The loader issues the equivalent statement with autocommit enabled,
-- because CREATE DATABASE cannot run inside a transaction block.

SELECT 'CREATE DATABASE eesaala_tracker ENCODING ''UTF8'' TEMPLATE template0'
WHERE NOT EXISTS (SELECT 1 FROM pg_database WHERE datname = 'eesaala_tracker');
-- In psql you can execute the generated statement with:  \gexec
