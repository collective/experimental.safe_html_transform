from Products.validation.validators import initialize
from Products.validation.ZService import ZService as Service

validation = Service()

initialize(validation)
