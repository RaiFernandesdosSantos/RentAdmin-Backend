"""Configurações para testes — roda os testes em SQLite em memória.

Uso:  python manage.py test --settings=core.settings_test
"""
from .settings import *  # noqa: F401,F403

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

## Captura e-mails em memória para assertions
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
