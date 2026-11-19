"""Creates the .env file with new random passwords and keys. Run it once:  python genereaza_env.py

Nobody needs to remember these values: Django and Docker read them from .env. If you ever need
one (for example the admin password), open .env. git ignores the file, so it stays on this computer.
"""
import secrets
import sys
from pathlib import Path

ENV = Path(__file__).resolve().parent / ".env"

if ENV.exists():
    sys.exit(".env already exists. Delete it first if you really want new values.")


def aleator(lungime):
    # letters, digits, - and _ only, so no character needs escaping in .env
    return secrets.token_urlsafe(lungime)


ENV.write_text(
    f"""# Made by genereaza_env.py. Never commit this file.

DJANGO_SECRET_KEY={aleator(50)}
DJANGO_DEBUG=true
DJANGO_ALLOWED_HOSTS=127.0.0.1,localhost

# The PostgreSQL container (compose.yaml)
POSTGRES_PASSWORD={aleator(24)}
DB_NAME=resonance
DB_USER=resonance_user
DB_PASSWORD={aleator(24)}
DB_HOST=127.0.0.1
DB_PORT=5433

# Used by: python manage.py createsuperuser --noinput
DJANGO_SUPERUSER_USERNAME=admin
DJANGO_SUPERUSER_EMAIL=admin@resonance.example
DJANGO_SUPERUSER_PASSWORD={aleator(12)}
""",
    encoding="utf-8",
)
print("Created .env. The admin login is in it (DJANGO_SUPERUSER_USERNAME and DJANGO_SUPERUSER_PASSWORD).")
