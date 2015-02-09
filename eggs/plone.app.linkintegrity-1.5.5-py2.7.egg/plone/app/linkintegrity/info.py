from plone.app.linkintegrity.interfaces import ILinkIntegrityInfo
from zope.interface import implements
from zope.component import queryUtility
from Acquisition import aq_base
from Products.CMFCore.interfaces import IPropertiesTool

try:
    from plone.uuid.interfaces import IUUID
    IUUID       # make pyflakes happy
except ImportError:
    # Archetypes-only fallback for Plone < 4.1
    def IUUID(obj, default=None):
        if hasattr(aq_base(obj), 'UID'):
            return obj.UID()
        else:
            return default


class LinkIntegrityInfo(object):
    """ adapter for browserrequests to temporarily store information
        related to link integrity in the request object """
    implements(ILinkIntegrityInfo)

    attribute = marker = 'link_integrity_info'

    def __init__(self, context):
        self.context = context      # the context is the request

    def integrityCheckingEnabled(self):
        """ determine if link integrity checking for the site is enabled """
        ptool = queryUtility(IPropertiesTool)
        enabled = False
        if ptool is not None:
            props = getattr(ptool, 'site_properties', None)
            if props is not None:
                enabled = props.getProperty('enable_link_integrity_checks', False)
        return enabled

    def getIntegrityInfo(self):
        """ return stored information regarding link integrity """
        return getattr(self.context, self.attribute, {})

    def setIntegrityInfo(self, info):
        """ store information regarding link integrity """
        setattr(self.context, self.attribute, info)

    def addBreach(self, source, target):
        """ convenience helper; see interface """
        breaches = self.getIntegrityInfo().get('breaches', {})
        breaches.setdefault(target, set()).add(source)
        self.setIntegrityBreaches(breaches)

    def getIntegrityBreaches(self):
        """
        return stored information regarding link integrity breaches.
        The information are in the form of a dictionary, they keys are the
        target objects relations that will be broken after a delete, the value
        is a list of source objects pointing to the target.
        """
        uuids_to_delete = [IUUID(obj, None) for obj in self.getDeletedItems()]
        uuids_to_delete = set(filter(None, uuids_to_delete))    # filter `None`
        breaches = dict(self.getIntegrityInfo().get('breaches', {}))
        # Do an in-place filtering of breaches, any source of a breach that
        # is to be removed anyway does not constitute a breach
        for target, sources in breaches.items():
            for source in list(sources):
                if IUUID(source) in uuids_to_delete:
                    sources.remove(source)
        # After the cleanup, there can be breaches to targets that have no
        # sources left. Also, targets where we confirm the link break are not
        # breaches any more, so we remove them too.
        for target, sources in breaches.items():
            if not sources or self.isConfirmedItem(target):
                del breaches[target]
        return breaches

    def setIntegrityBreaches(self, breaches):
        """ store information regarding link integrity breaches """
        info = self.getIntegrityInfo()
        info['breaches'] = breaches
        self.setIntegrityInfo(info)     # unnecessary, but sticking to the api

    def getDeletedItems(self):
        """ return information about all items deleted during the request """
        return self.getIntegrityInfo().get('deleted', set())

    def addDeletedItem(self, item):
        """ remember an item deleted during the request """
        info = self.getIntegrityInfo()
        info.setdefault('deleted', set()).add(item)
        self.setIntegrityInfo(info)     # unnecessary, but sticking to the api

    def getEnvMarker(self):
        """ return the marker string used to pass the already confirmed
            items across the retry exception """
        return self.marker

    def confirmedItems(self):
        """ return internal list of confirmed items """
        confirmed = self.context.environ.get(self.marker, [])
        if confirmed == 'all':
            confirmed = ['all']
        elif confirmed:
            s = confirmed.decode('base64')
            # split colon-delimited list of 8-byte oids
            confirmed = [s[i * 9:i * 9 + 8] for i in range(len(s) / 9 + 1)]
        return confirmed

    def isConfirmedItem(self, obj):
        """ indicate if the removal of the given object was confirmed """
        confirmed = self.confirmedItems()
        return obj._p_oid in confirmed or 'all' in confirmed

    def encodeConfirmedItems(self, additions):
        """ return the list of previously confirmed (for removeal) items,
            optionally adding the given items, encoded for usage in a form """
        confirmed = self.confirmedItems()
        for obj in additions:
            confirmed.append(obj._p_oid)
        return ":".join(confirmed).encode('base64')

    def moreEventsToExpect(self):
        attr = 'link_integrity_events_counter'
        counter = getattr(self.context, attr, 0) + 1    # nr of events so far
        setattr(self.context, attr, counter)            # save for next time
        expected = self.context.get('link_integrity_events_to_expect', 0)
        return counter < expected
