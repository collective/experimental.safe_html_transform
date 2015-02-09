from Products.Archetypes.public import *

class Blob(BaseContent):

    schema = BaseSchema + Schema((
        StringField('astring'),
        FileField('afile'),
        TextField('atext'),
        ImageField('aimage'),
        ))

registerType(Blob, 'tests.Marshall')
