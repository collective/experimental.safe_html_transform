from BaseFormAction import BaseFormAction

from Products.CMFFormController.FormController import registerFormAction
from ZPublisher.Publish import call_object, missing_name, dont_publish_class
from ZPublisher.mapply import mapply
import urlparse

def factory(arg):
    """Create a new traverse-to action"""
    return TraverseTo(arg)


class TraverseTo(BaseFormAction):
    def __call__(self, controller_state):
        url = self.getArg(controller_state)
        # see if this is a relative url or an absolute
        if len(urlparse.urlparse(url)[1]) != 0:
            # host specified, so url is absolute.  No good for traversal.
            raise ValueError, 'Can\'t traverse to absolute url %s' % str(url)

        url_path = urlparse.urlparse(url)[2]
        # combine args from query string with args from the controller state
        # (args in the state supercede those in the query string)
        args = self.combineArgs(url, controller_state.kwargs)

        # put the args in the REQUEST
        REQUEST = controller_state.getContext().REQUEST
        for (key, value) in args.items():
            REQUEST.set(key, value)

        # make sure target exists
        context = controller_state.getContext()
        obj = context.restrictedTraverse(url_path, default=None)
        if obj is None:
            raise ValueError, 'Unable to find %s\n' % str(url_path)
        return mapply(obj, REQUEST.args, REQUEST,
                               call_object, 1, missing_name, dont_publish_class,
                               REQUEST, bind=1)


registerFormAction('traverse_to',
                   factory,
                   'Traverse to the URL specified in the argument (a TALES expression).  The URL must be a relative URL.')
