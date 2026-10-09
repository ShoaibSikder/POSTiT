
import os

from .base import *

DEBUG = False

SECRET_KEY = os.environ["DJANGO_SECRET_KEY"]

ALLOWED_HOSTS = [
    host.strip()
    for host in os.environ["DJANGO_ALLOWED_HOSTS"].split(",")
    if host.strip()
]

# Configure these to match the deployed frontend and backend domains.
CSRF_TRUSTED_ORIGINS = [
    origin.strip()
    for origin in os.environ.get(
        "DJANGO_CSRF_TRUSTED_ORIGINS", ""
    ).split(",")
    if origin.strip()
]

SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
SECURE_REFERRER_POLICY = "same-origin"