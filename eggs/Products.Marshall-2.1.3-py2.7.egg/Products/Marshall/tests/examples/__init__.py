# import this
from Products.Archetypes.public import listTypes, process_types

import person
import blob
process_types(listTypes('tests.Marshall'), 'tests.Marshall')
