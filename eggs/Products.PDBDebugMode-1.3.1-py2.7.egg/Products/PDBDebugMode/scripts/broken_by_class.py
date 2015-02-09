from OFS import Uninstalled

broken = {}
for path, obj in app.ZopeFind(app, search_sub=True):
    if isinstance(obj, Uninstalled.BrokenClass):
        broken.setdefault(obj.__class__, []).append(path)

import pprint
pprint.pprint(broken)
