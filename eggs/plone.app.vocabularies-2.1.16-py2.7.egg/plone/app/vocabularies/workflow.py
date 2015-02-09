# -*- coding:utf-8 -*-
from zope.i18n import translate
from zope.i18nmessageid import MessageFactory
from zope.interface import implements
from zope.schema.interfaces import IVocabularyFactory
from zope.schema.vocabulary import SimpleTerm
from zope.schema.vocabulary import SimpleVocabulary
from zope.site.hooks import getSite

from Acquisition import aq_get
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.utils import safe_unicode

_ = MessageFactory('plone')


class WorkflowsVocabulary(object):
    """Vocabulary factory for workflows.

      >>> from zope.component import queryUtility
      >>> from plone.app.vocabularies.tests.base import create_context
      >>> from plone.app.vocabularies.tests.base import DummyTool

      >>> name = 'plone.app.vocabularies.Workflows'
      >>> util = queryUtility(IVocabularyFactory, name)
      >>> context = create_context()

      >>> class Workflow(object):
      ...     def __init__(self, id, title):
      ...         self.id = id
      ...         self.title = title

      >>> tool = DummyTool('portal_workflow')
      >>> def values():
      ...     return (Workflow('default', 'Default Workflow'),
      ...             Workflow('intranet', 'Intranet Workflow'),
      ...             Workflow('noticias', 'Workflow de Notícias'),)
      >>> tool.values = values
      >>> context.portal_workflow = tool

      >>> workflows = util(context)
      >>> workflows
      <zope.schema.vocabulary.SimpleVocabulary object at ...>

      >>> len(workflows.by_token)
      3

      >>> intranet = workflows.by_token['intranet']
      >>> intranet.title, intranet.token, intranet.value
      (u'Intranet Workflow', 'intranet', 'intranet')

      >>> noticias = workflows.by_token['noticias']
      >>> noticias.title == 'Workflow de Notícias'.decode('utf-8')
      True
    """
    implements(IVocabularyFactory)

    def __call__(self, context):
        items = []
        site = getSite()
        wtool = getToolByName(site, 'portal_workflow', None)
        if wtool is not None:
            items = [(w.title, w.id) for w in wtool.values()]
            items.sort()
            # All vocabularies return theirs term title as unicode
            items = [SimpleTerm(i[1], i[1], safe_unicode(i[0]))
                                                 for i in items]
        return SimpleVocabulary(items)

WorkflowsVocabularyFactory = WorkflowsVocabulary()


class WorkflowStatesVocabulary(object):
    """Vocabulary factory for workflow states.

      >>> from zope.component import queryUtility
      >>> from plone.app.vocabularies.tests.base import create_context
      >>> from plone.app.vocabularies.tests.base import DummyTool

      >>> name = 'plone.app.vocabularies.WorkflowStates'
      >>> util = queryUtility(IVocabularyFactory, name)
      >>> context = create_context()

      >>> tool = DummyTool('portal_workflow')
      >>> def listWFStatesByTitle(filter_similar=None):
      ...     return (('Private', 'private'),
      ...             ('Revisão', 'revisao'),
      ...             ('Published', 'published'))
      >>> tool.listWFStatesByTitle = listWFStatesByTitle
      >>> context.portal_workflow = tool

      >>> states = util(context)
      >>> states
      <zope.schema.vocabulary.SimpleVocabulary object at ...>

      >>> len(states.by_token)
      3

      >>> pub = states.by_token['published']
      >>> pub.title, pub.token, pub.value
      (u'Published [published]', 'published', 'published')

      >>> rev = states.by_token['revisao']
      >>> rev.title == 'Revisão [revisao]'.decode('utf-8')
      True
    """
    implements(IVocabularyFactory)

    def __call__(self, context):
        site = getSite()
        wtool = getToolByName(site, 'portal_workflow', None)
        if wtool is None:
            return SimpleVocabulary([])

        # XXX This is evil. A vocabulary shouldn't be request specific.
        # The sorting should go into a separate widget.

        # we get REQUEST from wtool because context may be an adapter
        request = aq_get(wtool, 'REQUEST', None)

        items = wtool.listWFStatesByTitle(filter_similar=True)
        items = [(safe_unicode(i[0]), i[1]) for i in items]
        items_dict = dict([(i[1], translate(_(i[0]), context=request))
                                                  for i in items])
        items_list = [(k, v) for k, v in items_dict.items()]
        items_list.sort(lambda x, y: cmp(x[1], y[1]))
        terms = [SimpleTerm(k, title=u'%s [%s]' % (v, k))
                                                  for k, v in items_list]
        return SimpleVocabulary(terms)

WorkflowStatesVocabularyFactory = WorkflowStatesVocabulary()


class WorkflowTransitionsVocabulary(object):
    """Vocabulary factory for workflow transitions

      >>> from zope.component import queryUtility
      >>> from plone.app.vocabularies.tests.base import create_context
      >>> from plone.app.vocabularies.tests.base import DummyTool

      >>> name = 'plone.app.vocabularies.WorkflowTransitions'
      >>> util = queryUtility(IVocabularyFactory, name)
      >>> context = create_context()

      >>> class Transition(object):
      ...     def __init__(self, id, actbox_name):
      ...         self.id = id
      ...         self.actbox_name = actbox_name

      >>> class TransitionsFolder(object):
      ...     def __init__(self, values):
      ...         self._values = values
      ...     def values(self):
      ...         return self._values

      >>> class Workflow(object):
      ...     def __init__(self, id, title, values):
      ...         self.id = id
      ...         self.title = title
      ...         self.transitions = TransitionsFolder(values)

      >>> tool = DummyTool('portal_workflow')
      >>> t1 = Transition('publish', 'Publish')
      >>> t2 = Transition('reject', 'Reject')
      >>> t3 = Transition('publicacao', 'Publicação')

      >>> wf1 = Workflow('default', 'Default Workflow', (t1, t2))
      >>> wf2 = Workflow('intranet', 'Intranet Workflow', (t1, ))
      >>> wf3 = Workflow('noticias', 'Workflow de Notícias', (t2, t3))

      >>> def values():
      ...     return (wf1, wf2, wf3)
      >>> tool.values = values
      >>> context.portal_workflow = tool

      >>> transitions = util(context)
      >>> transitions
      <zope.schema.vocabulary.SimpleVocabulary object at ...>

      >>> len(transitions.by_token)
      3

      >>> pub = transitions.by_token['publish']
      >>> pub.title, pub.token, pub.value
      (u'Publish [publish]', 'publish', 'publish')

      >>> publ = transitions.by_token['publicacao']
      >>> publ.title == 'Publicação [publicacao]'.decode('utf-8')
      True
    """
    implements(IVocabularyFactory)

    def __call__(self, context):
        site = getSite()
        wtool = getToolByName(site, 'portal_workflow', None)
        if wtool is None:
            return SimpleVocabulary([])

        transitions = {}
        for wf in wtool.values():
            transition_folder = getattr(wf, 'transitions', None)
            wf_name = wf.title or wf.id
            if transition_folder is not None:

                for transition in transition_folder.values():

                    # zope.i18nmessageid will choke
                    # if undecoded UTF-8 bytestrings slip through
                    # which we may encounter on international sites
                    # where transition names are in local language.
                    # This may break overlying functionality even
                    # if the terms themselves are never used
                    name = safe_unicode(transition.actbox_name)

                    transition_title = translate(
                                        _(name),
                                        context=aq_get(wtool, 'REQUEST', None))
                    transitions.setdefault(transition.id, []).append(
                        dict(title=transition_title, wf_name=wf_name))
        items = []
        transition_items = transitions.items()
        transition_items.sort(key=lambda transition: transition[0])
        for transition_id, info in transition_items:
            titles = set([i['title'] for i in info])
            item_title = ' // '.join(sorted(titles))
            item_title = "%s [%s]" % (item_title, transition_id)
            items.append(SimpleTerm(transition_id, transition_id, item_title))

        return SimpleVocabulary(items)

WorkflowTransitionsVocabularyFactory = WorkflowTransitionsVocabulary()
