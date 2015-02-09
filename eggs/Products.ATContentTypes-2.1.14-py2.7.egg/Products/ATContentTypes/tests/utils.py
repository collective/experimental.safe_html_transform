from AccessControl import ClassSecurityInfo
from App.class_init import InitializeClass
from App.Common import package_home
from DateTime import DateTime
from UserDict import UserDict
import ExtensionClass
import os

PACKAGE_HOME = package_home(globals())


class FakeRequestSession(ExtensionClass.Base, UserDict):
    """Dummy dict like object with set method for SESSION and REQUEST
    """
    security = ClassSecurityInfo()
    security.setDefaultAccess('allow')
    security.declareObjectPublic()

    def __init__(self):
        UserDict.__init__(self)
        # add a dummy because request mustn't be empty for test
        # like 'if REQUEST:'
        self['__dummy__'] = None

    def __nonzero__(self):
        return True

    def set(self, key, value):
        self[key] = value

InitializeClass(FakeRequestSession)
FakeRequestSession()


def dcEdit(obj):
    """dublin core edit (inplace)
    """
    obj.setTitle('Test title')
    obj.setDescription('Test description')
    obj.setSubject('Test subject')
    obj.setContributors(('test user a',))
    obj.setEffectiveDate(DateTime() - 1)
    obj.setExpirationDate(DateTime() + 2)
    obj.setFormat('text/structured')
    obj.setLanguage('de')
    obj.setRights('GPL')

from Products.validation import ValidationChain
EmptyValidator = ValidationChain('isEmpty')
EmptyValidator.appendSufficient('isEmpty')
idValidator = ValidationChain('isValidId')
idValidator.appendSufficient('isEmptyNoError')
idValidator.appendRequired('isValidId')
TidyHTMLValidator = ValidationChain('isTidyHtmlChain')
TidyHTMLValidator.appendRequired('isTidyHtmlWithCleanup')
NotRequiredTidyHTMLValidator = ValidationChain('isTidyHtmlNotRequiredChain')
NotRequiredTidyHTMLValidator.appendSufficient('isEmptyNoError')
NotRequiredTidyHTMLValidator.appendRequired('isTidyHtmlWithCleanup')
URLValidator = ValidationChain('isURL')
URLValidator.appendSufficient('isEmptyNoError')
URLValidator.appendRequired('isURL')
EmailValidator = ValidationChain('isEmailChain')
EmailValidator.appendSufficient('isEmptyNoError')
EmailValidator.appendSufficient('isMailto')
EmailValidator.appendRequired('isEmail')
EmailValidator = ValidationChain('isEmailChain')
EmailValidator.appendSufficient('isEmptyNoError')
EmailValidator.appendRequired('isEmail')
PhoneValidator = ValidationChain('isPhoneChain')
PhoneValidator.appendSufficient('isEmptyNoError')
PhoneValidator.appendRequired('isInternationalPhoneNumber')

PREFIX = os.path.abspath(os.path.dirname(__file__))


def input_file_path(file):
    return os.path.join(PREFIX, 'input', file)
