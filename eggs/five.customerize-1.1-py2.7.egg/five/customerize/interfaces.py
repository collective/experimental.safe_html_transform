from zope.interface import Interface


class ITTWViewTemplate(Interface):
    """ ttw customizable page template view """

    def __call__(context, request):
        """ render the template/view """


class IViewTemplateContainer(Interface):
    """ container for all ttw view template objects """

    def addTemplate(id, template):
        """ add the given ttw view template to the container
            and return it acquisition wrapped in the container """

