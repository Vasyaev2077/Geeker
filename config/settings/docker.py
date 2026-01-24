from .base import *  # noqa

# Docker dev stack: use Postgres/Redis from base.py, but keep local HTTP/dev-friendly security.
DEBUG = True
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
SECURE_HSTS_SECONDS = 0

# Email (password reset etc.) - print emails to container logs in docker dev
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
DEFAULT_FROM_EMAIL = "Geeker <no-reply@localhost>"

