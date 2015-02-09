from zope.interface import Interface

class IDateComponents(Interface):
    """A view that provides some helper methods useful in date widgets.
    """
    
    def result(date=None,
               use_ampm=0,
               starting_year=None,
               ending_year=None,
               future_years=None,
               minute_step=5):
        """Returns a dict with date information.
        """

