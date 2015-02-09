from z3c.form.field import Fields
from z3c.form.util import expandPrefix

from plone.z3cform.fieldsets.group import GroupFactory

def add(form, *args, **kwargs):
    """Add one or more fields. Keyword argument 'index' can be used to
    specify an index to insert at. Keyword argument 'group' can be used
    to specify the label of a group, which will be found and used or
    created if it doesn't exist.
    """

    index = kwargs.pop('index', None)
    group = kwargs.pop('group', None)

    new_fields = Fields(*args, **kwargs)

    if not group or isinstance(group, basestring):
        source = find_source(form, group=group)
    else:
        source = group

    if source is None and group:
        source = GroupFactory(group, new_fields)
        form.groups.append(source)
    else:
        if index is None or index >= len(source.fields):
            source.fields += new_fields
        else:
            field_names = source.fields.keys()
            source.fields = source.fields.select(*field_names[:index]) + \
                            new_fields + \
                            source.fields.select(*field_names[index:])

def remove(form, field_name, prefix=None):
    """Get rid of a field. The omitted field will be returned.
    """

    if prefix:
        field_name = expandPrefix(prefix) + field_name

    if field_name in form.fields:
        field = form.fields[field_name]
        form.fields = form.fields.omit(field_name)
        return field
    else:
        for group in form.groups:
            if field_name in group.fields:
                field = group.fields[field_name]
                group.fields = group.fields.omit(field_name)
                return field

def move(form, field_name, before=None, after=None, prefix=None, relative_prefix=None):
    """Move the field with the given name before or after another field.
    """
    if prefix:
        field_name = expandPrefix(prefix) + field_name

    if before and after:
        raise ValueError(u"Only one of 'before' or 'after' is allowed")

    offset = 0
    if after:
        offset = 1

    relative = orig_relative = before or after
    if relative_prefix:
        relative = expandPrefix(relative_prefix) + relative

    if field_name not in form.fields:
        found = False
        for group in getattr(form, 'groups', []):
            if field_name in group.fields:
                found = True
                break
        if not found:
            raise KeyError("Field %s not found" % field_name)

    if relative != '*' and relative not in form.fields:
        found = False
        for group in form.groups:
            if relative in group.fields:
                found = True
                break
        if not found:
            raise KeyError("Field %s not found" % relative)

    field = remove(form, field_name)

    group = None
    index = None

    if relative in form.fields:
        index = form.fields.keys().index(relative)
    elif orig_relative == '*' and relative_prefix is None:
        if before:
            index = 0
        else:
            index = len(form.fields.keys()) - 1
    else:
        for group in form.groups:
            if relative in group.fields:
                index = group.fields.keys().index(relative)
                break
            elif orig_relative == '*' and relative_prefix == group.prefix:
                if before:
                    index = 0
                else:
                    index = len(group.fields.keys()) - 1

    if index is None:
        raise KeyError("Field %s not found" % relative)

    add(form, field, group=group, index=index+offset)

def find_source(form, group=None):
    if group is not None:
        group_factory = [g for g in form.groups if g.__name__ == group]
        if len(group_factory) >= 1:
            return group_factory[0]
        else:
            return None
    return form
