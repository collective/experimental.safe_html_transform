import os

DEP_KEY = 'Z3C_AUTOINCLUDE_DEPENDENCIES_DISABLED'
PLUGIN_KEY = 'Z3C_AUTOINCLUDE_PLUGINS_DISABLED'

def dependencies_disabled():
    return os.environ.has_key(DEP_KEY)
def disable_dependencies():
    os.environ[DEP_KEY] = 'True'
def enable_dependencies():
    del os.environ[DEP_KEY]

def plugins_disabled():
    return os.environ.has_key(PLUGIN_KEY)
def disable_plugins():
    os.environ[PLUGIN_KEY] = 'True'
def enable_dependencies():
    del os.environ[PLUGIN_KEY]
