from Products.Archetypes.Storage import AttributeStorage

def migrateField(obj, action, newObj=None, **kwargs):
    """Migrate an Archetypes field

    - 'obj' should be the object to migrate from
    - 'newObj', if given, should be the object to migrate to. If not given,
        migration happens within obj only. If 'newObj' is given, attributes
        will not be unset on obj even if a 'newFieldName' for an action is
        specified.
    - 'action' specifies an action to apply to the object. It should be a dict,
        with the keys:

            - fieldName (required)
            - storage (optional; default = AttributeStorage)
            - callBefore
            - transform
            - newFieldName
            - newStorage (optional; default = same as 'storage')
            - unset (optional; default False)
            - callAfter

        For each object found by the query, the migrator will test for the
        existence of a field given by 'fieldName' stored using 'storage', an
        Archetypes storage, which defaults to AttributeStorage.

        If this field is found in the given storage, migration of will take
        place.

        If 'newFieldName' is given, this gives the new field name to store using
        'newStorage', if given. If 'newStorage' is not given, it defaults to
        the same storage as 'storage'.

        If 'newFieldName' is not given but 'newStorage' is, this is equivalent
        to switching the storage on a field.

        If callBefore is given, it is called before migration. This should be
        method with the signature:

            callBefore(obj, fieldName, value, **kwargs)

        If this returns True, migration continues. If it returns False, migration
        of this field is skipped.

        If 'transform' is given, this is used to transform the value of the
        attribute between the two attributes. This should be a method with the
        following signature

            transform(obj, value, **kwargs)

        The kwargs will contain any passed-in kwargs, as well as the fields
        'oldFieldName', 'newObj', 'newFieldName'. Note that 'newObj' and
        'newFieldName' may be the same as 'obj' and 'oldFieldName',
        respectively, if no object- or fieldname-migration is taking place.

        This method should return the transformed value of the field. If
        'transform' isgiven and 'newFieldName' is not, the return value from
        transform() is stored back in 'fieldName'.

        If 'unset' is given and is True, the old field is unset from the old
        object, always. This can be used to unset a field when there is no
        newFieldName. Note that 'unset' overrides 'transform', 'newFieldName',
        and 'newStorage'. If 'unset' is given, the value is unset, full stop.

        Finally, if 'callAfter' is given, it is called with the same arguments
        as callBefore().

    Returns True if the field was migrated, False otherwise.
    """

    fieldName = action['fieldName']
    storage = action.get('storage', AttributeStorage())
    newStorage = action.get('newStorage', None)
    callBefore = action.get('callBefore', None)
    transform = action.get('transform', None)
    newFieldName = action.get('newFieldName', None)
    callAfter = action.get('callAfter', None)
    unsetField = action.get('unset', False)

    if newObj is None or obj.getPhysicalPath() == newObj.getPhysicalPath():
        newObj = obj

    if newFieldName is None:
        newFieldName = fieldName

    if newStorage is None:
        newStorage = storage

    doTransform = True
    if transform is None:
        doTransform = False

    try:
        value = storage.get(fieldName, obj)
    except AttributeError:
        return False

    # Call and test callBefore, if given
    if callBefore is not None:
        status = callBefore(obj, fieldName, value, **kwargs)
        if not status:
            return False

    # Unset the old value. We may immediately re-set with the same storage
    # and/or the same fieldName, but this keeps things simple. Also note
    # that we unset the old storage on the possibly new object in case it
    # ended up there during blind attribute migration or initialisation
    storage.unset(fieldName, obj)
    try: storage.unset(fieldName, newObj)
    except (AttributeError, KeyError): pass

    # If we are simply unsetting, skip setting values
    if not unsetField:
        # Apply transform, if given
        if doTransform:
            value = transform(obj, value, fieldName = fieldName,
                                          newObj = newObj,
                                          newFieldName = newFieldName, **kwargs)

        # Now set the possibly transformed value, with the possibly new field name
        # and/or storage on the possibly new object, unless 'unset' is given.
        newStorage.set(newFieldName, newObj, value)

    # Call callAfter, if given
    if callAfter is not None:
        callAfter(newObj, fieldName, value, **kwargs)

    return True
