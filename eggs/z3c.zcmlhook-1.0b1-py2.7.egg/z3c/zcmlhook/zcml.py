from zope.interface import Interface
from zope import schema
from zope.configuration.fields import GlobalObject

class ICustomActionDirective(Interface):
    
    handler = GlobalObject(
            title=u"Function to execute",
            description=u"This function will be executed during ZCML processing",
            default=None,
            required=True,
        )
    
    order = schema.Int(
            title=u"Execution order",
            description=u"Set to a high number to execute late, or a negative number to execute early",
            default=0,
            required=False,
        )
    
    discriminator = schema.ASCIILine(
            title=u"Custom discriminator",
            description=u"By default, the full dotted name to the handler "
                        u"function is used as the discriminator. If you want "
                        u"to use the same function more than once, or if you "
                        u"want to override a custom action defined elsewhere "
                        u"with an overrides.zcml, you can set the "
                        u"discriminator explicitly.",
            default=None,
            required=False,
        )

def customAction(_context, handler, order=0, discriminator=None):
    if discriminator is None:
        discriminator = "%s.%s" % (handler.__module__, handler.__name__,)
    
    _context.action(
            discriminator=("executeCustomFunction", discriminator),
            callable=handler,
            args=(),
            order=order)
