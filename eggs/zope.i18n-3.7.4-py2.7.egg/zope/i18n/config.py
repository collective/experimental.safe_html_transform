import os

COMPILE_MO_FILES_KEY = 'zope_i18n_compile_mo_files'
COMPILE_MO_FILES = os.environ.get(COMPILE_MO_FILES_KEY, False)

ALLOWED_LANGUAGES_KEY = 'zope_i18n_allowed_languages'
ALLOWED_LANGUAGES = os.environ.get(ALLOWED_LANGUAGES_KEY, None)

if ALLOWED_LANGUAGES is not None:
    ALLOWED_LANGUAGES = ALLOWED_LANGUAGES.strip().replace(',', ' ')
    ALLOWED_LANGUAGES = frozenset(ALLOWED_LANGUAGES.split())
