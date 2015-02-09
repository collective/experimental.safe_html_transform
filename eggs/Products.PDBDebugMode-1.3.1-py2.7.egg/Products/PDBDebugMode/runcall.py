import pdb

from ZPublisher import Publish

try:
    # XXX Check for PlacelessTranslationService monkeypatch
    from Products.PlacelessTranslationService import PatchStringIO
    PatchStringIO # pyflakes
except ImportError:
    real_publish = Publish.publish
else:
    real_publish = Publish.old_publish

def resolveDottedName(dotted_name):
    """Resolve the dotted name importing as necessary then using
    getattr."""
    g = globals()
    l = locals()

    idx = dotted_name.find('.')
    if idx == -1:
        base_name = dotted_name
        rest_path = []
    else:
        base_name = dotted_name[:idx]
        rest_path = dotted_name[idx+1:].split('.')

    obj = __import__(base_name)

    for name in rest_path:
        obj = getattr(obj, name)

    return obj

def pdb_runcall(object, args, request):
    """If the request has the pdb_runcall key then we run the result
    of request traversal in the debugger.  Othwise, do it normally.

    A cookie for pdb_runcall may also be set or removed if the request
    has the toggle_runcall key."""
    response = request.response

    if request.has_key('toggle_runcall') and request.toggle_runcall:
        runcall_cookie = request.cookies.get('pdb_runcall', False)
        if runcall_cookie:
            response.expireCookie('pdb_runcall')
            return Publish.call_object(object, args, request) 
        else:
            response.setCookie('pdb_runcall', 1)

    if request.has_key('set_runcall_ignore'):
        if request.set_runcall_ignore:
            for ignore in request.set_runcall_ignore:
                response.appendCookie('runcall_ignore', ignore)
        else:
            response.expireCookie('runcall_ignore')
            
    if request.has_key('pdb_runcall'):
        if request.pdb_runcall:
            ignores = request.get('runcall_ignore', [])
            if ignores:
                ignores = ignores.split(':')
            for ignore in ignores:
                obj = resolveDottedName(ignore)
                if obj.im_func is getattr(object, 'im_func', None):
                    break
            else:
                return pdb.runcall(object, *args)

    return Publish.call_object(object, args, request) 

def pdb_publish(request, module_name, after_list, debug=0,
                call_object=pdb_runcall,
                missing_name=Publish.missing_name,
                dont_publish_class=Publish.dont_publish_class,
                mapply=Publish.mapply, ):
    """Hook the publish function to override the function used to call
    the result of the request traversal."""
    return real_publish(request, module_name, after_list, debug=0,
                call_object=call_object,
                missing_name=missing_name,
                dont_publish_class=dont_publish_class,
                mapply=mapply, )
