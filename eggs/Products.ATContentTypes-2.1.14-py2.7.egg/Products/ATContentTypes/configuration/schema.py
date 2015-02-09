import os

from ZConfig.datatypes import Registry
from ZConfig.loader import SchemaLoader
from Products.ATContentTypes.configuration import datatype

# schema file
DIR = os.path.dirname(os.path.abspath(__file__))
SCHEMA_FILE_NAME = 'schema.xml'
SCHEMA_FILE = os.path.join(DIR, SCHEMA_FILE_NAME)

# registry
# ATCT is using its own datatypes registry to add additional
# handlers.
atctRegistry = Registry()
atctRegistry.register('permission', datatype.permission_handler)
atctRegistry.register('identifer_none', datatype.identifier_none)
atctRegistry.register('byte-size-in-mb', datatype.byte_size_in_mb)
atctRegistry.register('image-dimension', datatype.image_dimension)
atctRegistry.register('image-dimension-or-no', datatype.image_dimension_or_no)
atctRegistry.register('pil-algo', datatype.pil_algo)

# schema
atctSchema = None


def loadSchema(file, registry=atctRegistry, overwrite=False):
    """Loads a schema file

    * file
      A path to a file
    * registry
      A ZConfig datatypes registry instance
    * overwrite
      Overwriting the existing global schema is not possible unless overwrite
      is set to true. Useful only for unit testing.
    """
    global atctSchema
    if atctSchema is not None and not overwrite:
        raise RuntimeError, 'Schema is already loaded'
    schemaLoader = SchemaLoader(registry=registry)
    atctSchema = schemaLoader.loadURL(file)
    return atctSchema

loadSchema(SCHEMA_FILE)

__all__ = ('atctSchema',)
