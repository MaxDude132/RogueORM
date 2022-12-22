from rogue.errors import ValidationError


class NotAKnownFieldException(Exception):
    pass


class DataNotFetchedException(Exception):
    pass


class MissingFieldValueError(Exception):
    pass


class FieldValidationError(ValidationError):
    pass


class ModelValidationError(ValidationError):
    pass
