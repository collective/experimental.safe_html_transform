from RegexValidator import RegexValidator
from RangeValidator import RangeValidator
from ExpressionValidator import ExpressionValidator

validators = []

from BaseValidators import baseValidators
validators.extend(baseValidators)

from EmptyValidator import validatorList
validators.extend(validatorList)

from SupplValidators import validatorList
validators.extend(validatorList)

from IdValidator import validatorList
validators.extend(validatorList)


def initialize(service):
    for validator in validators:
        service.register(validator)
