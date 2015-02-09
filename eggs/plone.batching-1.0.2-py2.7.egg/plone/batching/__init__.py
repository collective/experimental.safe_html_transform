from plone.batching.batch import Batch

from AccessControl import allow_class
from AccessControl import allow_module

allow_module('plone.batching')
allow_class(Batch)
