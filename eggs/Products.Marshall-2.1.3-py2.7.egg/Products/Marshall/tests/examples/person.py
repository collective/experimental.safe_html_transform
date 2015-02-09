from Products.Archetypes.public import *

class Person(BaseContent):

    schema = BaseSchema + Schema((
        ReferenceField('parents',
                       relationship='my_parents',
                       multiValued=True),
        ReferenceField('children',
                       relationship='my_children',
                       multiValued=True),
        ReferenceField('father',
                       relationship='my_father',
                       multiValued=False,
                       required=False),
        ReferenceField('mother',
                       relationship='my_mother',
                       multiValued=False,
                       required=False),
        LinesField('food_preference',
                   accessor='getFoodPrefs',
                   mutator='setFoodPrefs'),
        ))

registerType(Person, 'tests.Marshall')
