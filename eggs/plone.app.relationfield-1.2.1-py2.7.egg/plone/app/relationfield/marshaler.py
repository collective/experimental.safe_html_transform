from plone.rfc822.defaultfields import BaseFieldMarshaler
from z3c.relationfield import RelationValue

class RelationFieldMarshaler(BaseFieldMarshaler):
    """Field marshaler for z3c.relationfield IRelation and IRelationChoice
    fields
    """
    
    ascii = True
    
    def encode(self, value, charset='utf-8', primary=False):
        if value is None:
            return None
        return str(value.to_id)
    
    def decode(self, value, message=None, charset='utf-8', contentType=None, primary=False):
        try:
            toId = int(value.decode(charset))
        except TypeError, e:
            raise ValueError(e)
        return RelationValue(toId)
