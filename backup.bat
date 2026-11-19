@echo off
rem Backs up the data of every table defined in instruments/models.py, as INSERT commands.
rem
rem   backup.bat
rem
rem It writes backups\backup_<date>_<time>.sql. Run it from the project folder, with the
rem database container running (docker compose up -d). To load a backup into the database:
rem
rem   restaurare.bat backups\backup_<date>_<time>.sql

setlocal
rem work in the folder of this file, where compose.yaml is, wherever it was started from
cd /d "%~dp0"

rem The date and time for the file's name. %date% is written differently on every Windows
rem language, so PowerShell (part of Windows) formats it the same everywhere.
for /f %%t in ('powershell -NoProfile -Command "Get-Date -Format yyyy-MM-dd_HH-mm-ss"') do set ACUM=%%t

if not exist backups mkdir backups
set FISIER=backups\backup_%ACUM%.sql

rem pg_dump runs inside the PostgreSQL container, so nothing needs installing on Windows, and
rem the container lets it in without a password.
rem   --data-only                only the rows: the tables themselves come from the migrations
rem   --inserts                  one INSERT command per row (pg_dump's default is COPY)
rem   --column-inserts           INSERT INTO table (column, ...) VALUES (...), so a backup still
rem                              loads after a column is added to the table
rem   --table "instruments_*"    only the tables of instruments/models.py (Django names them
rem                              app_model), with their link tables and id counters. Django's own
rem                              tables (sessions, permissions, migrations) are made by migrate.
rem Since lab 6, pg_dump warns about "circular foreign-key constraints": a department's head is an
rem employee, and an employee works in a department. restaurare.bat handles that; see docs\lab6.md.
docker compose exec -T db pg_dump --username=resonance_user --dbname=resonance --data-only --inserts --column-inserts --no-owner --no-privileges --table "public.instruments_*" > "%FISIER%"
if errorlevel 1 (
    del "%FISIER%" 2>nul
    echo.
    echo The backup failed. Is the database running? Start it with: docker compose up -d
    exit /b 1
)

rem count the INSERT lines: one per saved row
for /f %%n in ('find /c "INSERT INTO" ^< "%FISIER%"') do set RANDURI=%%n
echo Saved %RANDURI% rows in %FISIER%
endlocal
