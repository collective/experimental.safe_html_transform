import transaction
from AccessControl import SecurityManagement

SecurityManagement.newSecurityManager(
    None, app.acl_users.getUser('admin'))

for path, obj in app.ZopeFind(app, search_sub=True,
                              obj_expr="id=='broken'"):
    try:
        split_path = path.rsplit('/', 1)
        if len(split_path) == 2:
            container_path, broken_id = split_path
            container = app.unrestrictedTraverse(container_path)
        else:
            container = app
            broken_id, = split_path
        if broken_id in container.objectIds():
            if container.manage_delObjects is not None:
                container.manage_delObjects([broken_id])
    except:
        import pdb, sys; pdb.post_mortem(sys.exc_info()[2])
        raise
                
transaction.commit()
