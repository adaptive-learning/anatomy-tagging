# -*- coding: utf-8 -*-
"""
Django settings for anatomy_tagging project.

For more information on this file, see
https://docs.djangoproject.com/en/1.6/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.6/ref/settings/
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os
BASE_DIR = os.path.dirname(os.path.dirname(__file__))

ADMINS = (
    ('Vít Stanislav', 'slaweet@gmail.com'),
)
MANAGERS = ADMINS

SEND_BROKEN_LINK_EMAILS = True


ON_PRODUCTION = False
ON_STAGING = False

if 'PROSO_ON_PRODUCTION' in os.environ:
    ON_PRODUCTION = True
if 'PROSO_ON_STAGING' in os.environ:
    ON_STAGING = True
    DEBUG_TOOLBAR_PATCH_SETTINGS = False

if ON_PRODUCTION:
    DEBUG = False
else:
    DEBUG = True

ON_SERVER = ON_PRODUCTION or ON_STAGING

# Make a dictionary of default keys
default_keys = {
    'SECRET_KEY': '$7#bbg892g5)vpf$&va3b)m%w(x063awse+q+covv2c8i=)cpc'
}

# Replace default keys with dynamic values if we are on server
use_keys = default_keys
if ON_SERVER:
    default_keys['SECRET_KEY'] = os.environ['PROSO_SECRET_KEY']

# Make this unique, and don't share it with anybody.
SECRET_KEY = use_keys['SECRET_KEY']


TEMPLATE_DEBUG = True

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    os.path.join(BASE_DIR, 'anatomy_tagging', 'templates'),
)

ALLOWED_HOSTS = [
    'altest.thran.cz',
    'znackuj.anatom.cz',
]


# Application definition

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'anatomy_tagging',
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

ROOT_URLCONF = 'anatomy_tagging.urls'

WSGI_APPLICATION = 'anatomy_tagging.wsgi.application'

if ON_SERVER:
    MEDIA_DIR = os.path.join(BASE_DIR, '..', 'media')
else:
    MEDIA_DIR = BASE_DIR


# Database
# https://docs.djangoproject.com/en/1.6/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(MEDIA_DIR, 'db.sqlite3'),
    }
}

# Internationalization
# https://docs.djangoproject.com/en/1.6/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.6/howto/static-files/

STATIC_ROOT = os.path.join(BASE_DIR, '..', 'static')
STATIC_URL = '/static/'

STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
)


try:
    from githash import HASH
except (SyntaxError, ImportError) as e:
    HASH = ''
