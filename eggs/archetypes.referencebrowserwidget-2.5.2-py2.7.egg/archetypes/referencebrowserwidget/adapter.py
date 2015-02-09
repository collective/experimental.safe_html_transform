def ATReferenceAdapter(context, field):
    relationship = field.relationship
    items = [item.getTargetObject()
             for item in context.getReferenceImpl(relationship)]
    return [item for item in items if item is not None]


def ATBackReferenceAdapter(context, field):
    relationship = field.relationship
    items = [item.getTargetObject()
             for item in context.getBackReferenceImpl(relationship)]
    return [item for item in items if item is not None]


def PloneRelationsAdapter(context, field):
    relationship = field.relationship
    from plone.app.relations.interfaces import IRelationshipSource
    return IRelationshipSource(context).getTargets(relation=relationship)


def PloneRelationsRevAdapter(context, field):
    relationship = field.relationship
    from plone.app.relations.interfaces import IRelationshipTarget
    return IRelationshipTarget(context).getSources(relation=relationship)
