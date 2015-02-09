## Script (Python) "formatCatalogMetadata"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind subpath=traverse_subpath
##parameters=value,long_format=True
##title=Determine whether the input is a DateTime or ISO date and localize it if so, also convert lists and dicts into reasonable strings.
from DateTime import DateTime
from ZODB.POSException import ConflictError
from AccessControl import Unauthorized

if value is None:
    return ''

if same_type(value, DateTime()):
    return context.toLocalizedTime(value.timeTime(), long_format=long_format)

# Ugly but fast check for ISO format (ensure we have '-' and positions 4 and 7,
#  ' ' at position 10 and ':' and 13 and 16), then convert just in case.
if same_type(value, '') and (value[4:-1:3] == '-- ::' or value[4:-6:3] == '--T::'):
    try:
        DateTime(value)
    except ConflictError:
        raise
    except:
        # Bare excepts are ugly, but DateTime raises a whole bunch of different
        # errors for bad input (Syntax, Time, Date, Index, etc.), best to be
        # safe.
        return value
    return context.toLocalizedTime(value, long_format=long_format)

try:
    # Missing.Value and others have items() but don't have security assertions
    # to support accessing it.
    items = getattr(value, 'items', None)
except Unauthorized:
    items = None

if items is not None and callable(items):
    # For dictionaries return a string of the form 'key1: value1, key2: value2'
    value = ', '.join(['%s: %s' % (a, b) for a, b in items()])
if same_type(value, []) or same_type(value, ()):
    # Return list as comma separated values
    alist = []
    for item in value:
        if same_type(item, u''):
            alist.append(item)
        else:
            alist.append(str(item))
    value = ', '.join(alist)

if not same_type(value, u''):
    value = str(value)

pt = context.portal_properties
site_props = getattr(pt, 'site_properties', None)
if site_props is not None:
    max_length = site_props.getProperty(
        'search_results_description_length', 160)
    ellipsis = site_props.getProperty('ellipsis', '...')
else:
    max_length = 160
    ellipsis = '...'
if len(value) < max_length:
    return value
else:
    return '%s%s' % (value[:max_length], ellipsis)
