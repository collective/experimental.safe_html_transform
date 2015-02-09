from Products.validation.interfaces.IValidator import IValidationChain
from zope.interface import implements

from types import TupleType, ListType
from config import validation as validationService
from exceptions import ValidatorError

V_REQUIRED   = 1
V_SUFFICIENT = 2


class ValidationChain:
    """
    """
    implements(IValidationChain)

    def __init__(self, name, title='', description='', validators=(),
                 register=False):
        self.name = name
        self.title = title or name
        self.description = description
        self._v_mode = []
        self._chain = []

        if type(validators) not in (TupleType, ListType):
            validators = (validators, )
        for validator in validators:
            if type(validator) in (TupleType, ListType):
                self.append(validator[0], validator[1])
            else:
                self.appendRequired(validator)

        if register:
            validationService.register(self)

    def __repr__(self):
        """print obj support
        """
        map = { V_REQUIRED : 'V_REQUIRED', V_SUFFICIENT : 'V_SUFFICIENT' }
        val = []
        for validator, mode in self:
            name = validator.name
            val.append("('%s', %s)" % (name, map.get(mode)))
        return '(%s)' % ', '.join(val)

    def __len__(self):
        """len(obj) support
        """
        return len(self._chain)

    def __iter__(self):
        """Python 2.3 for i in x support
        """
        return iter(zip(self._chain, self._v_mode))

    def __cmp__(self, key):
        if isinstance(key, ValidationChain):
            str = repr(key)
        else:
            str = key
        return cmp(repr(self), str)

    def __getitem__(self, idx):
        """self[idx] support and Python 2.1 for i in x support
        """
        return self._chain[idx], self._v_mode[idx]

    def append(self, id_or_obj, mode=V_REQUIRED):
        """Appends a validator
        """
        validator = self.setValidator(id_or_obj)
        self.setMode(validator, mode)

    def appendRequired(self, id_or_obj):
        """Appends a validator as required
        """
        self.append(id_or_obj, mode=V_REQUIRED)

    def appendSufficient(self, id_or_obj):
        """Appends a validator as sufficient
        """
        self.append(id_or_obj, mode=V_SUFFICIENT)

    def insert(self, id_or_obj, mode=V_REQUIRED, position=0):
        """Inserts a validator at position (default 0)
        """
        validator = self.setValidator(id_or_obj, position=position)
        self.setMode(validator, mode, position=position)

    def insertRequired(self, id_or_obj, position=0):
        """Inserts a validator as required at position (default 0)
        """
        self.insert(id_or_obj, mode=V_REQUIRED, position=0)

    def insertSufficient(self, id_or_obj, position=0):
        """Inserts a validator as sufficient at position (default 0)
        """
        self.insert(id_or_obj, mode=V_SUFFICIENT, position=0)

    def setMode(self, validator, mode, position=None):
        """Set mode
        """
        # validator not required
        if position is None:
            self._v_mode.append(mode)
        else:
            self._v_mode.insert(position, mode)

    def setValidator(self, id_or_obj, position=None):
        """Set validator
        """
        validator = validationService.validatorFor(id_or_obj)

        if position is None:
            self._chain.append(validator)
        else:
            self._chain.insert(position, validator)

        return validator

    def __call__(self, value, *args, **kwargs):
        """Do validation
        """
        results = {}
        failed = False
        if len(self) == 1:
            mode = [m for (v, m) in self][0]
            if mode == V_SUFFICIENT:
                # There is only one validator and its mode is
                # 'sufficient' which means it does not have to
                # validate.  So we cut the validation short.
                return True # validation was successful

        for validator, mode in self:
            name = validator.name
            result = validator(value, *args, **kwargs)
            if result == True:
                if mode == V_SUFFICIENT:
                    return True # validation was successful
                elif mode == V_REQUIRED:
                    continue    # go on
                else:
                    raise ValidatorError, 'Unknown mode %s' % mode
            else:
                if mode == V_SUFFICIENT:
                    if isinstance(result, basestring):
                        # don't log if validator doesn't return an error msg
                        results[name] = result
                    continue # no fatal error, go on
                elif mode == V_REQUIRED:
                    if isinstance(result, basestring):
                        # don't log if validator doesn't return an error msg
                        results[name] = result
                    failed = True
                    break    # fatal error, stop and fail
                else:
                    raise ValidatorError, 'Unknown mode %s' % mode

        if failed:
            return '\n'.join([
                              #'%s: %s' % (name, res)
                              '%s' % res
                              for name, res in results.items()]
                            )
        else:
            return True
