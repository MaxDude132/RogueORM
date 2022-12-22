from rogue.errors import ValidationError


class ExecutionError(Exception):
    pass


class ManagerValidationError(ValidationError):
    pass
