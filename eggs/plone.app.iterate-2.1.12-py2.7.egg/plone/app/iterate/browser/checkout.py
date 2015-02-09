##################################################################
#
# (C) Copyright 2006 ObjectRealms, LLC
# All Rights Reserved
#
# This file is part of iterate.
#
# iterate is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# iterate is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with iterate; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
##################################################################

from zope.component import getMultiAdapter, getAdapters

from Acquisition import aq_inner
from Products.Five.browser import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from ZODB.POSException import ConflictError

from Products.statusmessages.interfaces import IStatusMessage

from plone.app.iterate import PloneMessageFactory as _
from plone.app.iterate.interfaces import ICheckinCheckoutPolicy
from plone.app.iterate.interfaces import CheckoutException
from plone.app.iterate.interfaces import IWCContainerLocator
from plone.app.iterate.interfaces import IObjectArchiver

class Checkout(BrowserView):
    
    index = ViewPageTemplateFile('checkout.pt')
    
    def containers(self):
        """Get a list of potential containers
        """
        context = aq_inner(self.context)
        for name, locator in getAdapters((context,), IWCContainerLocator):
            if locator.available:
                yield dict(name=name, locator=locator)
    
    def __call__(self):
        context = aq_inner(self.context)

        containers = list(self.containers())
        if len(containers) == 1:
            # Special case for when there's only when folder to select
            self.request.form['form.button.Checkout'] = 1
            self.request.form['checkout_location'] = containers[0]['name']

        # We want to redirect to a specific template, else we might
        # end up downloading a file
        if self.request.form.has_key('form.button.Checkout'):
            control = getMultiAdapter((context, self.request), name=u"iterate_control")
            if not control.checkout_allowed():
                raise CheckoutException(u"Not allowed")

            location = self.request.form.get('checkout_location', None)
            locator = None
            try:
                locator = [c['locator'] for c in self.containers() if c['name'] == location][0]
            except IndexError:
                IStatusMessage(self.request).addStatusMessage(_("Cannot find checkout location"), type='stop')
                view_url = context.restrictedTraverse("@@plone_context_state").view_url()
                self.request.response.redirect(view_url)
                return

            policy = ICheckinCheckoutPolicy(context)
            wc = policy.checkout(locator())
            
            # we do this for metadata update side affects which will update lock info
            context.reindexObject('review_state')
            
            IStatusMessage(self.request).addStatusMessage(_("Check-out created"), type='info')
            view_url = wc.restrictedTraverse("@@plone_context_state").view_url()
            self.request.response.redirect(view_url)
        elif self.request.form.has_key('form.button.Cancel'):
            view_url = context.restrictedTraverse("@@plone_context_state").view_url()
            self.request.response.redirect(view_url)
        else:
            return self.index()
