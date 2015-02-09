"""This module contains some functions that may be helpful in the
implementation of IObjectPath interface.
"""

def path(root, obj):
    steps = []
    orig_obj = obj
    while obj is not None:
        steps.append(obj.__name__)
        if obj is root:
            break
        obj = obj.__parent__
    else:
        raise ValueError("Cannot create path for %s" % orig_obj)
    steps.reverse()
    return '/' + '/'.join(steps)

def resolve(root, path):
    steps = path.split('/')
    assert steps[0] == ''
    obj = root
    if steps[1] == '':
        return root
    assert steps[1] == root.__name__
    steps = steps[2:]
    for step in steps:
        try:
            obj = obj[step]
        except KeyError:
            raise ValueError("Cannot resolve path %s" % path)
    return obj

        
