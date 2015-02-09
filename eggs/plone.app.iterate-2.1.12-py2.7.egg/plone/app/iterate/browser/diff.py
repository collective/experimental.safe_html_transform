"""
$Id: diff.py 1807 2007-02-06 06:52:46Z hazmat $
"""

from Products.CMFCore.utils import getToolByName
from Products.Five.browser import BrowserView

from plone.app.iterate.interfaces import IWorkingCopy, IBaseline
from plone.app.iterate.relation import WorkingCopyRelation

class DiffView( BrowserView ):

    def __init__( self, context, request ):
        self.context = context
        self.request = request
        if IBaseline.providedBy( self.context ):
            self.baseline = context
            self.working_copy = context.getBackReferences( WorkingCopyRelation.relationship )[0]
        elif IWorkingCopy.providedBy( self.context ):
            self.working_copy = context
            self.baseline = context.getReferences( WorkingCopyRelation.relationship )[0]
        else:
            raise AttributeError("Invalid Context")

    def diffs( self ):
        diff = getToolByName(self.context, 'portal_diff')
        return diff.createChangeSet( self.baseline,
                                     self.working_copy,
                                     id1="Baseline",
                                     id2="Working Copy" )
    
        
    

    
