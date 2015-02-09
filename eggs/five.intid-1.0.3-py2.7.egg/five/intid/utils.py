from Acquisition import aq_base, aq_inner, IAcquirer

def aq_iter(obj, error=None):
    if not (IAcquirer.providedBy(obj) or hasattr(obj, '__parent__')):
        raise TypeError("%s not acquisition wrapped" %obj)

    # adapted from alecm's 'listen'
    seen = set()
    # get the inner-most wrapper (maybe save some cycles, and prevent
    # bogus loop detection)
    cur = aq_inner(obj)
    while cur is not None:
        yield cur
        seen.add(id(aq_base(cur)))
        cur = getattr(cur, 'aq_parent', getattr(cur, '__parent__', None))
        if id(aq_base(cur)) in seen:
            # avoid loops resulting from acquisition-less views
            # whose __parent__ points to
            # the context whose aq_parent points to the view
            if error is not None:
                raise error, '__parent__ loop found'
            break

