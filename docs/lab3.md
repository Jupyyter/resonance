# Lab 3: models, PostgreSQL, admin, GitHub

## 1. First, commit Labs 1 and 2 (before extracting this zip)

The lab wants one commit per stage from now on, so save the current state as its own commit. In the folder with `manage.py`:

```
git init
git add .
git status
```

`git status` lists what will be committed. `.venv`, `.env` and `db.sqlite3` must not be in it (`.gitignore` keeps them out). Then:

```
git commit -m "Laboratoarele 1-2: pagini, template-uri, meniu, jurnal de accesari, diagrama bazei de date"
```

If git asks who you are, run these once, then commit again:

```
git config --global user.name "Your Name"
git config --global user.email "the email of your GitHub account"
```

This commit still has the old `SECRET_KEY` written in `settings.py`. That's fine: from Lab 3 the key lives in `.env`, and `genereaza_env.py` makes a new one, so the old one stops being used.

## 2. Install Docker Desktop

PostgreSQL runs in a Docker container, so it doesn't need installing on Windows, and you never type a database password. Install Docker Desktop from docker.com (free for personal and educational use) and start it. If it asks to enable WSL 2, accept and restart.

## 3. Extract the zip and install the new packages

Extract over the project and overwrite. This time `settings.py` is included: it no longer holds any secret, because it reads them from `.env`.

```
pip install -r requirements.txt
```

That adds `psycopg` (Python's PostgreSQL driver), `pillow` (needed by `ImageField`) and `python-dotenv` (reads `.env`).

## 4. Make the .env file and start PostgreSQL

```
python genereaza_env.py
docker compose up -d
```

`genereaza_env.py` writes `.env` with new random values: Django's secret key, the database passwords and an admin login. You don't need to remember any of them: Django and Docker read them from `.env`, and if you ever need one, open the file.

`docker compose up -d` starts PostgreSQL as described in `compose.yaml`. The first time, it downloads the PostgreSQL 18 image (about 150 MB), creates the database, and runs `creare_user.sql`, which creates `resonance_user` and the `resonance` database. `docker compose ps` should show the `db` service as `healthy`.

After that, PostgreSQL starts by itself whenever Docker Desktop is running. The data stays between restarts, in a Docker volume.

## 5. Create the tables, the superuser, and log in

```
python manage.py migrate
python manage.py createsuperuser --noinput
python manage.py runserver
```

`migrate` runs `instruments/migrations/0001_initial.py`, which creates the tables, constraints and indexes. `createsuperuser --noinput` takes the username and password from `.env` (`DJANGO_SUPERUSER_USERNAME` and `DJANGO_SUPERUSER_PASSWORD`). Open http://127.0.0.1:8000/admin/ and log in with them.

`python manage.py test instruments` runs the tests on PostgreSQL, including the model rules.

**Starting over**: `docker compose down -v` deletes the container and all its data. The next `docker compose up -d` starts from an empty database and runs `creare_user.sql` again. That's also needed if you regenerate `.env`, because the user's password is only set when the database is first created.

## 6. Load the data

```
python manage.py incarca_date
```

It reads `date_exemplu/date.json` and adds 6 categories, 6 brands, 5 distributors, 5 services, 10 instruments and 5 recordings. The audio files in `date_exemplu/inregistrari/` are copied into `media/`, as if uploaded. Every row is checked with the same rules as the admin before it's saved, and if one is wrong, nothing is saved and the message says which row and why. Running it again updates the rows instead of adding copies, so after editing `date.json`, just run it again.

The lab says the rows are entered "folosind interfața admin". They show up in the admin exactly as if typed there, but be ready to add one row live at the presentation (see section 9).

## 7. Commit Lab 3 and put it on GitHub

```
git add .
git status
git commit -m "Laborator 3: modele, PostgreSQL in Docker, admin"
```

On github.com, create a new repository named `resonance`, without a README. Then:

```
git remote add origin https://github.com/YOUR-USERNAME/resonance.git
git branch -M main
git push -u origin main
```

Before committing, `git status` must not list `.env` or `media`. Put the repository's link in the activity table. For each later stage: `git add .`, then `git commit -m "Laborator N: ..."` and `git push`.

## 8. Where each Task 1 requirement is (instruments/models.py)

| Requirement | Where |
|---|---|
| 5 fields that accept null | Brand.website, Brand.founded_year, Distributor.phone, Instrument.weight_kg, Instrument.image, Instrument.distributor |
| A unique field other than id | Category.name, Brand.name, Distributor.name, Distributor.email, Service.name |
| EmailField, URLField or SlugField | Distributor.email (EmailField), Brand.website (URLField) |
| Default ordering for 2 models | every model's `Meta.ordering`, for example categories by display order, instruments newest first |
| A field with choices | Instrument.condition (new, used, refurbished), Recording.sound (clean, amplified, with effects) |
| 4 defaults, one that can be left empty in the admin | Category.color, icon, display_order; Instrument.stock, condition, left_handed, date_added; Service.duration_days, available; Recording.sound. Can be left empty (`blank=True`): Instrument.materials, Service.description |
| 5 help texts | Category.color, icon, display_order; Brand.founded_year; Distributor.phone; Service.price, duration_days; Instrument.price, left_handed, weight_kg, materials, distributor, services; Recording.number, audio_file, duration_s |
| A datetime that defaults to the moment it's added | Instrument.date_added (`default=timezone.now`) |
| 5 fields with error messages | Category.name, Brand.name, Brand.website, Distributor.email, Instrument.name, Instrument.price, Recording.title |
| 5 constraints with models.Q | 9 `CheckConstraint`s: category colour, brand founding year, distributor phone, service price and duration, instrument price, weight, used-is-single and new-has-distributor, recording number and duration |
| 4 indexed fields | Instrument: name, price, condition, date_added (`Meta.indexes`) |
| ImageField or FileField | Instrument.image (ImageField), Recording.audio_file (FileField) |

Task 2: correct plural names come from `verbose_name_plural` (Django would write "Categorys"), and each model's admin list is set with `list_display` in `instruments/admin.py`.

## 9. For the presentation

**Adding a row in the admin**: if asked, add one live, for example a category named "Folk instruments" (a description is required; colour, icon and order are already filled in). It takes a minute, and it's the natural moment to show the help texts and to trigger a couple of the error messages below.

**Where help texts show**: in the admin's add and change forms, in small grey text under the field's label. Price, Distributor, Left handed, Weight and Materials on the Add instrument page are good examples.

**Error messages you can trigger** (all appear in red above the field or the form):

| Do this | Message |
|---|---|
| Add a category with an existing name | There's already a category with this name. |
| Save a category without a name | Give the category a name. |
| Brand website: `fender` | Enter the full address, starting with https://. |
| Distributor email: `nope` | This isn't a valid email address. |
| Save an instrument without a name | Every instrument needs a name. |
| Category colour: `red` | The colour must be # followed by 6 hex digits, like #2D6B5D. |
| A new instrument without a distributor | A new instrument needs the distributor it came from. |
| Instrument price 0 | The price must be greater than 0. |
| A used instrument with stock 3 | A used or refurbished instrument is one of a kind: stock 0 or 1. |
| Brand founded in 1500 | The founding year must be 1600 or later. |

**The database user from creare_user.sql** (Task 2). Show the file, then the container's log of its first start, where the file ran:

```
docker compose logs db
```

It contains `running /docker-entrypoint-initdb.d/creare_user.sql`, followed by `CREATE ROLE`, `CREATE DATABASE` and `ALTER ROLE`. To list the users: `docker compose exec db psql -U postgres -c "\du"`. Inside the container no password is needed, which is also how you can look into the database any time.

**Constraints exist in PostgreSQL too.** Run `docker compose exec db psql -U resonance_user -d resonance -c "\d instruments_instrument"`. The indexes are listed, then a "Check constraints" section with each `CheckConstraint` by name. Django checks them first to show a readable message, and PostgreSQL rejects bad data even if it doesn't come through Django.

**Recording is the weak entity**: it's edited inside its instrument's page, and `UniqueConstraint(instrument, number)` makes the number unique only within one instrument. Deleting an instrument deletes its recordings (`on_delete=CASCADE`).
