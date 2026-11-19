-- Creates the PostgreSQL user the Django app connects with, and the project's database.
--
-- You don't run it by hand: the PostgreSQL container (compose.yaml) runs it with psql, the
-- PostgreSQL command line, the first time it starts, as the "postgres" superuser.
-- The lines starting with a backslash are psql commands, not SQL.

-- Stop at the first error instead of carrying on with the next statements.
\set ON_ERROR_STOP on

-- The password comes from the DB_PASSWORD environment variable (set from .env by compose.yaml),
-- so it's never written in this file, which goes on GitHub.
\getenv parola DB_PASSWORD

-- :'parola' inserts the variable as a quoted SQL string
CREATE USER resonance_user WITH PASSWORD :'parola';

-- The user owns the database, so Django can create its tables there.
CREATE DATABASE resonance OWNER resonance_user ENCODING 'UTF8';

-- Lets "python manage.py test" create and drop its temporary test database.
ALTER USER resonance_user CREATEDB;
