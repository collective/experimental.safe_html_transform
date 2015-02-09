from Products.CMFCore.utils import ContentInit
from Products.Archetypes.atapi import process_types, listTypes
from Products.CMFCore.permissions import AddPortalContent
from archetypes.referencebrowserwidget.config import PROJECTNAME
from archetypes.referencebrowserwidget.config import WITH_SAMPLE_TYPES
from archetypes.referencebrowserwidget.widget import ReferenceBrowserWidget

ReferenceBrowserWidget  # pyflakes


def initialize(context):
    import demo
    demo  # pyflakes
    content_types, constructors, ftis = process_types(
        listTypes(PROJECTNAME),
        PROJECTNAME)

    ContentInit(
        PROJECTNAME + ' Content',
        content_types = content_types,
        permission = AddPortalContent,
        extra_constructors = constructors,
        ).initialize(context)

if WITH_SAMPLE_TYPES:
    # setup sample types
    from Products.GenericSetup import EXTENSION, profile_registry
    profile_registry.registerProfile('referencebrowserwidget_sampletypes',
        'ReferenceBrowserWidget Sample Content Types',
        'Extension profile including referencebrowserwidget sample content types',
        'profiles/sample_types',
        'archetypes.referencebrowserwidget',
        EXTENSION)
