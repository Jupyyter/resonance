@echo off
rem Loads a backup made by backup.bat into the database.
rem
rem   restaurare.bat backups\backup_2026-11-19_13-05-00.sql
rem
rem The tables must exist already (python manage.py migrate). Their rows are replaced by the
rem backup's, so loading the same backup twice gives the same result.

setlocal
cd /d "%~dp0"

if "%~1"=="" (
    echo Which backup? For example: restaurare.bat backups\backup_2026-11-19_13-05-00.sql
    echo.
    echo The backups in the backups folder, newest first:
    dir /b /o:-d backups\*.sql 2>nul
    exit /b 1
)
if not exist "%~1" (
    echo There's no file %~1
    exit /b 1
)

rem psql, PostgreSQL's command line, runs inside the container:
rem   --command              first, empties every instruments_ table and resets its id counter
rem                          (the departments and message types made by migrate included: the
rem                          backup brings its own copies, with their heads). CASCADE also empties
rem                          the admin's history, whose rows point to users.
rem   --file=-               then runs the backup's commands, read from the file given here
rem   --single-transaction   all of it or none of it: if one row fails, nothing changes
rem   ON_ERROR_STOP=1        stop at the first error instead of carrying on
rem   --output=/dev/null     hide the results of the file's SELECT commands (errors still show)
rem Django creates its foreign keys as DEFERRABLE INITIALLY DEFERRED: PostgreSQL checks them at the
rem end of the transaction, so the order of the rows doesn't matter, not even for the department
rem and its head, who point at each other.
docker compose exec -T db psql --username=resonance_user --dbname=resonance --quiet --output=/dev/null --single-transaction --set=ON_ERROR_STOP=1 --command="SET client_min_messages = warning; DO $$ BEGIN EXECUTE (SELECT 'TRUNCATE ' || string_agg(quote_ident(tablename), ', ') || ' RESTART IDENTITY CASCADE' FROM pg_tables WHERE schemaname = 'public' AND left(tablename, 12) = 'instruments_'); END $$;" --file=- < "%~1"
if errorlevel 1 (
    echo.
    echo Nothing was changed. The message above says which row failed.
    exit /b 1
)
echo Loaded %~1
endlocal
