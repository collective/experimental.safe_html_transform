=========================
Plone ContentRules Engine
=========================

plone.contentrules is a pure Zope implementation of a content rules engine.
Content rules are managed by the user, and may be likened to email filter
rules or Apple's Automator. A user creates a Rule, and composes a sequence
of rule elements, specifically Conditions and Actions. Rules are assigned to
a context via a Rule Assignment Manager.

An event handler in the application layer (such as the complementary 
plone.app.contentrules package) will query a Rule Manager for all applicable
rules for this event, in this context, and execute them.

The architecture is pluggable - it is easy to provide new rule elements, which
can be registered via the <plone:ruleAction /> and <plone:ruleCondition />
ZCML directives (or manually as utilities providing IRuleElement).

Note that this package does not contain any UI for actual real-world rule
elements. plone.app.contentrules provides Zope 2 acrobatics and Plone-specific
elements and UI.

Defining new rule elements
--------------------------

Rules are composed of rule elements - actions and conditions. These will be
executed one by one when a rule is invoked.

First, we create some rule elements.

Lets start with some basic imports:

  >>> from zope.interface import Interface, implements
  >>> from zope.component import adapts
  >>> from zope.component import getUtility, getAllUtilitiesRegisteredFor
  >>> from zope import schema

  >>> from zope.component import provideUtility
  >>> from zope.component import provideAdapter

  >>> from plone.contentrules.rule.interfaces import IRuleCondition, IRuleAction
  >>> from plone.contentrules.rule.interfaces import IRuleElementData
  >>> from plone.contentrules.rule.element import RuleCondition, RuleAction
  
  >>> from persistent import Persistent
  
We create an interface describing the schema of the configuration of the custom 
rule element. This allows us to use zope.formlib to create add and edit forms,
for example.

  >>> class IMoveToFolderAction(Interface):
  ...     targetFolder = schema.TextLine(title=u"Target Folder")
  
Create the actual class for holding the configuration data. The element
and summary properties come from IRuleElementData and are used by the
user interface to discover the edit view and present a title and summery
to the user:
  
  >>> class MoveToFolderAction(Persistent):
  ...     implements(IMoveToFolderAction, IRuleElementData)
  ...     targetFolder = ''
  ...     element = "test.moveToFolder"
  ...     @property
  ...     def summary(self):
  ...         return "Move to folder " + self.targetFolder

In order to be able to execute the rule elements that form a rule, they must be
adaptable to IExecutable. This should be a multi-adapter from 
(context, element, event).

  >>> from plone.contentrules.rule.interfaces import IExecutable
  >>> from zope.component.interfaces import IObjectEvent
  
  >>> class MoveToFolderExecutor(object):
  ...     implements(IExecutable)
  ...     adapts(Interface, IMoveToFolderAction, IObjectEvent)
  ...     def __init__(self, context, element, event):
  ...         self.context = context
  ...         self.element = element
  ...         self.event = event
  ...     def __call__(self):
  ...         print "Tried to execute MoveToFolderExecutor, but not implemented"
  ...         return True

  >>> provideAdapter(MoveToFolderExecutor)

Returning True in the above executor means that rule execution may continue
with other elements

Using ZCML, a rule element will be created describing this rule. This will 
result in an object like the one below.

  >>> moveElement = RuleAction()
  >>> moveElement.title = "Move To Folder"
  >>> moveElement.description = "Move an object to a folder"
  >>> moveElement.for_ = Interface
  >>> moveElement.event = IObjectEvent
  >>> moveElement.addview = 'test.moveToFolder'
  >>> moveElement.editview = 'edit.html'
  >>> moveElement.schema = IMoveToFolderAction
  >>> moveElement.factory = MoveToFolderAction
  
The ZCML will register this as a utility providing IRuleAction.

  >>> provideUtility(moveElement, provides=IRuleAction, name="test.moveToFolder")
  >>> getUtility(IRuleAction, name="test.moveToFolder")
  <plone.contentrules.rule.element.RuleAction object at ...>

For the second example, we will create a rule element to log caught events.
First, let us make some sort of temporary logger:
  
  >>> import logging
  >>> logger = logging.getLogger("temporary_logger")
  >>> handler = logging.StreamHandler() #just stderr for the moment
  >>> formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s -  %(message)s")
  >>> handler.setFormatter(formatter)
  >>> logger.addHandler(handler)

Again, we have to define an interface for the logger action:

  >>> class ILoggerAction(Interface):
  ...     targetLogger = schema.TextLine(title=u"target logger",default=u"temporary_logger")
  ...     loggingLevel = schema.Int(title=u"logging level", default=1000)
  ...     loggerMessage = schema.TextLine(title=u"message",
  ...                                     description=u"&e = the triggering event, &c = the context",
  ...                                     default=u"caught &e at &c")

A factory class holding configuration data:
         
  >>> class LoggerAction(Persistent):
  ...     implements(ILoggerAction, IRuleElementData)
  ...     loggingLevel = ''
  ...     targetLogger = ''
  ...     message = ''
  ...     element = "test.logger"
  ...     summary = "Log a message"
 
As well as the executor that does the actual logging, capable of being adapted
to IExecutable. In this case, it will adapt any context and any event.

  >>> class LoggerActionExecutor(object):
  ...     implements(IExecutable)
  ...     adapts(Interface, ILoggerAction, Interface)
  ...    
  ...     def __init__(self, context, element, event):
  ...         self.context = context
  ...         self.element = element
  ...         self.event = event
  ...
  ...     def __call__(self):
  ...         logger = logging.getLogger(self.element.targetLogger)
  ...        
  ...         processedMessage = self.element.message.replace("&e", str(self.event))
  ...         processedMessage = processedMessage.replace("&c", str(self.context))
  ...   
  ...         logger.log(self.element.loggingLevel, processedMessage)
  ...         return True 

  >>> provideAdapter(LoggerActionExecutor)

This element will also be created using ZCML, but we will create it manually for
now:

  >>> loggerElement = RuleAction()
  >>> loggerElement.title = "Log Event"
  >>> loggerElement.description = "Log the caught event to a target log"
  >>> loggerElement.for_ = Interface
  >>> loggerElement.event = None
  >>> loggerElement.addview = 'test.logger'
  >>> loggerElement.editview = 'edit.html'
  >>> loggerElement.schema = ILoggerAction
  >>> loggerElement.factory = LoggerAction
  
  >>> provideUtility(loggerElement, provides=IRuleAction, name="test.logger")
  >>> getUtility(IRuleAction, name="test.logger")
  <plone.contentrules.rule.element.RuleAction object at ...>

As a condition, consider one which only executes rules if the context provides
a given interface.

  >>> from zope.interface import Attribute
  >>> class IInterfaceCondition(Interface):
  ...     iface = Attribute(u'the interface')

  >>> class InterfaceCondition(object):
  ...     implements (IInterfaceCondition, IRuleElementData)
  ...     iface = None
  ...     element = "test.interface"
  ...     @property
  ...     def summary(self):
  ...         return "Check for interface " + self.iface.__identifier__

  >>> class InterfaceConditionExecutor(object):
  ...     implements(IExecutable)
  ...     adapts(Interface, IInterfaceCondition, Interface)
  ...
  ...     def __init__(self, context, element, event):
  ...         self.context = context
  ...         self.element = element
  ...         self.event = event
  ...
  ...     def __call__(self):
  ...         return self.element.iface.providedBy(self.context)
  
  >>> provideAdapter(InterfaceConditionExecutor)

  >>> ifaceElement = RuleCondition()
  >>> ifaceElement.title = "Context interface condition"
  >>> ifaceElement.description = "Ensure the rule is only executed for certain interfaces"
  >>> ifaceElement.for_ = Interface
  >>> ifaceElement.event = None
  >>> ifaceElement.addview = 'test.interfaceCondition'
  >>> ifaceElement.editview = 'edit.html'
  >>> ifaceElement.schema = IInterfaceCondition
  >>> ifaceElement.factory = InterfaceCondition
  
  >>> provideUtility(ifaceElement, provides=IRuleCondition, name="test.interface")
  >>> getUtility(IRuleCondition, name="test.interface")
  <plone.contentrules.rule.element.RuleCondition object at ...>
  
Last, we will create a generic rule element that stops rule execution. The 
interface to this rule will not need to specify any fields, and the
configuration class will not need to hold any data - but they must still be 
present:

  >>> class IHaltExecutionAction(Interface):
  ...     pass

  >>> class HaltExecutionAction(Persistent):
  ...     implements (IHaltExecutionAction, IRuleElementData)
  ...     element = "test.halt"
  ...     summary = "Halt!"

  >>> class HaltExecutionExecutor(object):
  ...     implements(IExecutable)
  ...     adapts(Interface, IHaltExecutionAction, Interface)
  ...     # Above: the second "Interface" causes this
  ...     # element to be available for every event
  ...     def __init__(self, context, element, event):
  ...         self.context = context
  ...         self.element = element
  ...         self.event = event
  ...     def __call__(self):
  ...         print "Rule Execution aborted at HaltAction"
  ...         return False  # False = Stop Execution! This is the payload.
  
  >>> provideAdapter(HaltExecutionExecutor)

  >>> haltElement = RuleAction()
  >>> haltElement.title = "Halt Rule Execution"
  >>> haltElement.description = "Prevent further elements from executing for an event"
  >>> haltElement.for_ = Interface
  >>> haltElement.event = None
  >>> haltElement.addview = 'test.haltExecution'
  >>> haltElement.editview = 'edit.html'
  >>> haltElement.schema = IHaltExecutionAction
  >>> haltElement.factory = HaltExecutionAction
  
  >>> provideUtility(haltElement, provides=IRuleAction, name="test.halt")
  >>> getUtility(IRuleAction, name="test.halt")
  <plone.contentrules.rule.element.RuleAction object at ...>

Composing elements into rules
------------------------------

In the real world, the UI would most likely ask for all types of actions and
conditions applicable in the given context. The functions 
plone.app.engine.utils can help with this.

The default adapters reply on the IRuleContainer marker interface, which 
itself implies IAttributeAnnotatable.

  >>> from plone.contentrules.engine.interfaces import IRuleAssignable
  >>> class IMyContent(IRuleAssignable):
  ...     pass
  >>> class MyContent(object):
  ...     implements(IMyContent)
  
  >>> context = MyContent()

  >>> from plone.contentrules.engine import utils
  
The allAvailableActions() and allAvailableConditions() functions return those
actions or conditions applicable for a particular type of event.
  
  >>> availableActions = utils.allAvailableActions(IObjectEvent)
  >>> moveElement in availableActions
  True
  >>> loggerElement in availableActions
  True
  >>> haltElement in availableActions
  True
  
  >>> availableConditions = utils.allAvailableConditions(Interface)
  >>> ifaceElement in availableConditions
  True
  
Suppose the user selected the first action in this list and wanted to use it in
a rule:

  >>> selectedAction = availableActions[0]
  
At this point, the UI would use the 'addview' to create a form to configure the
instance of this rule element.

  >>> configuredAction = MoveToFolderAction()
  >>> configuredAction.targetFolder = "/foo"
  >>> configuredAction
  <MoveToFolderAction object at ...>

The element, once created, now needs to be saved as part of a rule.

  >>> from plone.contentrules.rule.rule import Rule
  >>> testRule = Rule()
  >>> testRule.title = "Fairly simple test rule"
  >>> testRule.description = "some test actions"
  >>> testRule.event = Interface
  >>> testRule.actions.append(configuredAction)
  
Rules can have many elements. To demonstrate, we will first add the element 
again, so it executes twice:

  >>> testRule.actions.append(configuredAction)

Additionally, we will manually add two halt actions, to see if rules really 
stop executing:

  >>> haltActionInstance = HaltExecutionAction()
  >>> testRule.actions.append(haltActionInstance)
  >>> testRule.actions.append(haltActionInstance)

The second halt action should never get executed.

This second test rule will be used to demonstrate how multiple rules get 
executed.

  >>> testRule2 = Rule()
  >>> testRule2.title = "A fairly simple test rule"
  >>> testRule2.description = "only containing a moveToFolderAction"
  >>> testRule2.event = Interface
  >>> testRule2.actions.append(configuredAction)

A third rule will be used to demonstrate a condition:

  >>> interfaceConditionInstance = InterfaceCondition()
  >>> interfaceConditionInstance.iface = IMyContent
  
  >>> moveToFolderAction = MoveToFolderAction()
  >>> moveToFolderAction.targetFolder = "/foo"
  
  >>> testRule3 = Rule()
  >>> testRule3.title = "A rule for IMyContent"
  >>> testRule3.description = "only execute on IMyContent"
  >>> testRule3.event = Interface
  >>> testRule3.conditions.append(interfaceConditionInstance)
  >>> testRule3.conditions.append(moveToFolderAction)

Managing rules relative to objects
----------------------------------

Rules are stored in an IRuleStorage - a local utility. Rules are then assigned
to a context by way of an IRuleAssignmentManager.

The rule storage is an ordered container. It is also marked with 
IContainerNamesContainer because by default, an INameChooser should be
used to pick a name for rules. This is simply because rules normally don't
have sensible names.
  
  >>> from plone.contentrules.engine.interfaces import IRuleStorage
  >>> from plone.contentrules.engine.storage import RuleStorage
  >>> from zope.component import provideUtility

  >>> ruleStorage = RuleStorage()
  >>> provideUtility(provides=IRuleStorage, component=ruleStorage)
  
  >>> from zope.container.interfaces import IOrderedContainer
  >>> from zope.container.interfaces import IContainerNamesContainer
  
  >>> IOrderedContainer.providedBy(ruleStorage)
  True
  >>> IContainerNamesContainer.providedBy(ruleStorage)
  True
  
  >>> len(ruleStorage)
  0
  
Before a rule is saved, it has no name, and no parent.

  >>> from zope.container.interfaces import IContained
  >>> IContained.providedBy(testRule)
  True
  >>> testRule.__name__ is None
  True
  >>> testRule.__parent__ is None
  True
  
After being saved, it will be given a name and parentage.
  
  >>> ruleStorage[u'testRule'] = testRule
  >>> testRule.__name__
  u'testRule'
  >>> testRule.__parent__ is ruleStorage
  True
  
We add the other rules too, so that they can be used later.

  >>> ruleStorage[u'testRule2'] = testRule2
  >>> ruleStorage[u'testRule3'] = testRule3

We now need to assign rules to the context. The assignments use the same
names as the rules, since a particular rule can be assigned to a particular
context only once.

  >>> from plone.contentrules.engine.interfaces import IRuleAssignmentManager
  >>> manager = IRuleAssignmentManager(context)
  
  >>> from plone.contentrules.engine.assignments import RuleAssignment
  >>> manager[testRule.__name__] = RuleAssignment(testRule.__name__, enabled=True, bubbles=False)

The enabled argument can turn off a given rule temporarily. The bubbles 
argument, if True, means that the rule will apply to events in subfolders,
not just the current folder.

  >>> manager[testRule2.__name__] = RuleAssignment(testRule2.__name__, enabled=False, bubbles=False)
  >>> manager[testRule3.__name__] = RuleAssignment(testRule3.__name__, enabled=True, bubbles=True)

Executing rules
---------------

An event can trigger rules bound to a context. The event will use an 
IRuleExecutor to do so. 
  
  >>> from plone.contentrules.engine.interfaces import IRuleExecutor
  >>> localRuleExecutor = IRuleExecutor(context)
  
The executor method will be passed an event, so that rules may determine what 
triggered them. Because this is a test, we registered the rule for the "event"
described by "Interface". In fact, this would equate to a rule triggered by
any and all events.

  >>> from zope.component.interfaces import ObjectEvent
  >>> someEvent = ObjectEvent(context)

  >>> localRuleExecutor(someEvent)
  Tried to execute MoveToFolderExecutor, but not implemented
  Tried to execute MoveToFolderExecutor, but not implemented
  Rule Execution aborted at HaltAction
  Tried to execute MoveToFolderExecutor, but not implemented

The first three output lines above are from the first rule, the fourth from the 
third rule. There was no output from the disabled rule.

Notice that the first rule does not bubble. The event handlers in the 
application layer should tell the executor this when it's executing rules
higher up. Rules that are assigned not to bubble will not be executed.

  >>> localRuleExecutor(someEvent, bubbled=True)
  Tried to execute MoveToFolderExecutor, but not implemented

Now consider what would happen if the interface condition failed:

  >>> class OtherContent(object):
  ...     implements(IRuleAssignable)
  >>> otherContext = OtherContent()
  
  >>> otherManager = IRuleAssignmentManager(otherContext)
  >>> otherManager[testRule3.__name__] = RuleAssignment(testRule3.__name__, enabled=True, bubbles=False)
  
  >>> otherRuleExecutor = IRuleExecutor(otherContext)
  >>> otherRuleExecutor(someEvent)

Notice that there was no output.
  
  >>> from zope.interface import directlyProvides
  >>> directlyProvides(otherContext, IMyContent)
  >>> otherRuleExecutor(someEvent)
  Tried to execute MoveToFolderExecutor, but not implemented
  
It is also possible to add more specific filters to which rules get executed.
Here is an example that filters out the duplicate rules.

  >>> class RuleDupeFilter(object):
  ...     executed = []
  ...     def __call__(self, context, rule, event):
  ...         if rule.__name__ in self.executed:
  ...             return False
  ...         else:
  ...             self.executed.append(rule.__name__)
  ...             return True
  
  >>> dupeFilter = RuleDupeFilter()
  >>> localRuleExecutor(someEvent, rule_filter=dupeFilter)
  Tried to execute MoveToFolderExecutor, but not implemented
  Tried to execute MoveToFolderExecutor, but not implemented
  Rule Execution aborted at HaltAction
  Tried to execute MoveToFolderExecutor, but not implemented
  >>> otherRuleExecutor(someEvent, rule_filter=dupeFilter)

The second rule executor will not execute the rule testRule3, since it was
already executed by the first one.
  
Event Filtering
---------------

Rule elements can be specific to certain events. To create some event-specific
rule elements, first import the specific events

  >>> from zope.component.interfaces import IObjectEvent, ObjectEvent
  >>> from zope.lifecycleevent.interfaces import IObjectCreatedEvent, \
  ...                                            IObjectCopiedEvent, \
  ...                                            IObjectModifiedEvent
 
The hierarchy for these events is:

Interface
- IObjectEvent
- - IObjectModifiedEvent
- - IObjectCreatedEvent
- - - IObjectCopiedEvent

An element for IObjectCreatedEvent:

  >>> class IObjectCreatedSpecificAction(Interface):
  ...     pass
  >>> class ObjectCreatedSpecificAction(Persistent):
  ...     implements (IObjectCreatedSpecificAction)
  >>> class ObjectCreatedExecutor(object):
  ...     implements(IExecutable)
  ...     adapts(Interface, IObjectCreatedSpecificAction, IObjectCreatedEvent) #!
  ...     def __init__(self, context, element, event):
  ...         self.context = context
  ...         self.element = element
  ...         self.event = event
  ...     def __call__(self):
  ...         return True
  >>> provideAdapter(ObjectCreatedExecutor)
  >>> objectCreatedSpecificElement = RuleAction()
  >>> objectCreatedSpecificElement.title = "Object Created specific action"
  >>> objectCreatedSpecificElement.description = "is only available for object created events"
  >>> objectCreatedSpecificElement.for_ = Interface       #!
  >>> objectCreatedSpecificElement.event = IObjectCreatedEvent #!
  >>> objectCreatedSpecificElement.addview = 'testing.created'
  >>> objectCreatedSpecificElement.editview = 'edit.html'
  >>> objectCreatedSpecificElement.schema = IObjectCreatedSpecificAction
  >>> objectCreatedSpecificElement.factory = ObjectCreatedSpecificAction
  >>> provideUtility(objectCreatedSpecificElement, provides=IRuleAction, name="test.objectcreated")
  >>> getUtility(IRuleAction, name="test.objectcreated")
  <plone.contentrules.rule.element.RuleAction object at ...>


An element for IObjectCopiedEvent:

  >>> class IObjectCopiedSpecificAction(Interface):
  ...     pass
  >>> class ObjectCopiedSpecificAction(Persistent):
  ...     implements (IObjectCopiedSpecificAction)
  >>> class ObjectCopiedExecutor(object):
  ...     implements(IExecutable)
  ...     adapts(Interface, IObjectCopiedSpecificAction, IObjectCopiedEvent) #!
  ...     def __init__(self, context, element, event):
  ...         self.context = context
  ...         self.element = element
  ...         self.event = event
  ...     def __call__(self):
  ...         return True
  >>> provideAdapter(ObjectCopiedExecutor)
  >>> objectCopiedSpecificElement = RuleAction()
  >>> objectCopiedSpecificElement.title = "Object Copied Specific Action"
  >>> objectCopiedSpecificElement.description = "is only available for object created events"
  >>> objectCopiedSpecificElement.for_ = Interface       #!
  >>> objectCopiedSpecificElement.event = IObjectCopiedEvent #!
  >>> objectCopiedSpecificElement.addview = 'testing.created'
  >>> objectCopiedSpecificElement.editview = 'edit.html'
  >>> objectCopiedSpecificElement.schema = IObjectCopiedSpecificAction
  >>> objectCopiedSpecificElement.factory = ObjectCopiedSpecificAction
  >>> provideUtility(objectCopiedSpecificElement, provides=IRuleAction, name="test.objectcopied")
  >>> getUtility(IRuleAction, name="test.objectcopied")
  <plone.contentrules.rule.element.RuleAction object at ...>

All elements so far, applicable for object events:

  >>> map(lambda x: x.title, utils.allAvailableActions(IObjectEvent))
  ['Move To Folder', 'Log Event', 'Halt Rule Execution']

For a more specific event, we may get more elements (i.e. those that also 
apply to more general events):

  >>> map(lambda x: x.title, utils.allAvailableActions(IObjectCopiedEvent))
  ['Move To Folder', 'Log Event', 'Halt Rule Execution', 'Object Created specific action', 'Object Copied Specific Action']
  >>> map(lambda x: x.title, utils.allAvailableActions(IObjectCreatedEvent))
  ['Move To Folder', 'Log Event', 'Halt Rule Execution', 'Object Created specific action']

Filtering for specific events:

  >>> from zope.lifecycleevent.interfaces import IObjectCreatedEvent, IObjectCopiedEvent
  >>> newContext = MyContent()
  
  >>> sorted([a.title for a in utils.getAvailableActions(context, IObjectEvent)])
  ['Halt Rule Execution', 'Log Event', 'Move To Folder']
  
  >>> sorted([a.title for a in utils.getAvailableActions(context, IObjectCreatedEvent)])
  ['Halt Rule Execution', 'Log Event', 'Move To Folder', 'Object Created specific action']
  
  >>> sorted([a.title for a in utils.getAvailableActions(context, IObjectCopiedEvent)])
  ['Halt Rule Execution', 'Log Event', 'Move To Folder', 'Object Copied Specific Action', 'Object Created specific action']
