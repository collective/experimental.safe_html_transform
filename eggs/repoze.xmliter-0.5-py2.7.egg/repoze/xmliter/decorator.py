from repoze.xmliter.serializer import XMLSerializer

def lazy(function=None, serializer=None, doctype=None):
    if function is not None:
        def decorator(*args, **kwargs):
            result = function(*args, **kwargs)
            return XMLSerializer(result, serializer, doctype=doctype)
    else:
        def decorator(function):
            return lazy(function=function, serializer=serializer, doctype=doctype)
    
    return decorator
