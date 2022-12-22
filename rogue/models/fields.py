from copy import deepcopy
from typing import get_args

from .errors import DataNotFetchedException, FieldValidationError


UNKNOWN_VALUE = "__UNKNOWN_VALUE__"

# Necessary so that we can reference Field in FieldMeta
Field = None


class FieldMeta(type):
    def __getitem__(self, item: type):
        if isinstance(item, tuple):
            assert len(item) == 1, "Only 1 item can be passed in the Field typing."
            item = item[0]

        args = get_args(item)
        nullable = type(None) in args
        assert (
            len(args) < 2 or len(args) == 2 and nullable
        ), f"Only union between a type and None is accepted."

        if args:
            type_ = [arg for arg in args if arg is not None][0]
        else:
            type_ = item

        return Field(type_, nullable=nullable)


class Field(metaclass=FieldMeta):
    def __init__(self, type_: type, nullable: bool = False):
        self.type: type = type_
        self.nullable: bool = nullable

        if type_ not in FIELD_MAPPING:
            raise TypeError(f"{type_} is not supported.")

        self._field = FIELD_MAPPING[self.type]

        self._kwargs = {}

    def __call__(self, *args, **kwargs):
        # This is necessary to allow the following syntax in the model:
        #     field_name: Field[str](max_char=5)
        if not args:
            self._kwargs.update(kwargs)
            return self

        kwargs.update(self._kwargs)
        return self._field(
            *args, python_type=self.type, nullable=self.nullable, **kwargs
        )


class BaseField:
    PYTHON_TYPE = None

    def __init__(self, parent, field_name, python_type=None, nullable=False, **kwargs):
        self._parent = parent
        self._name = field_name
        self.python_type = python_type or self.PYTHON_TYPE
        self.nullable = nullable
        self.default = None
        self.is_pk = kwargs.get("primary_key", False)

    def validate(self, value):
        if value is None and self.default:
            value = self.default

        if value is None and not self.nullable and not self.is_pk:
            raise FieldValidationError(f"Field {self._name} cannot be None.")

        if value is not None and not isinstance(value, self.PYTHON_TYPE):
            raise FieldValidationError(
                f"Field {self._name} can only accept type {self.PYTHON_TYPE}, {type(value)} was passed."
            )


class StringField(BaseField):
    PYTHON_TYPE = str

    def __init__(self, *args, **kwargs):
        self.max_char = kwargs.pop("max_char")
        super().__init__(*args, **kwargs)


class IntegerField(BaseField):
    PYTHON_TYPE = int


class FloatField(BaseField):
    PYTHON_TYPE = float


class ForeignKeyField(BaseField):
    PYTHON_TYPE = int


FIELD_MAPPING = {str: StringField, int: IntegerField, float: FloatField}
