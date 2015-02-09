from Testing import ZopeTestCase

from Products.SecureMailHost.SecureMailHost import SecureMailBase

try:
    True
except NameError:
    True=1
    False=0

ZopeTestCase.installProduct('MailHost', quiet=1)
ZopeTestCase.installProduct('PageTemplates', quiet=1)
ZopeTestCase.installProduct('PythonScripts', quiet=1)
ZopeTestCase.installProduct('ExternalMethod', quiet=1)
