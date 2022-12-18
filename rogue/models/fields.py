from typing import get_args

from rogue.fetchers import Fetcher


UNKNOWN_VALUE = "__UNKNOWN_VALUE__"

# Necessary so that we can reference Field in FieldMeta
Field = None


class FieldMeta(type):
    def __getitem__(self, item: type):
        if isinstance(item, tuple):
            assert len(item) == 1, "Only 1 item can be passed in the Field typing."
            item = item[0]

        args = get_args(item)
        nullable = None in args
        assert (
            len(args) <= 2 or len(args) == 2 and not nullable
        ), "Only union between a type and None is accepted."

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
        else:
            self._field = FIELD_MAPPING[self.type]

    def __call__(self, parent, field_name, **kwargs):
        return self._field(
            parent, field_name, python_type=self.type, nullable=self.nullable, **kwargs
        )


class BaseField:
    def __init__(self, parent, field_name, python_type=int, nullable=False, **kwargs):
        self._parent = parent
        self._name = field_name
        self.python_type = python_type
        self.nullable = nullable
        self.is_pk = kwargs.get("primary_key", False)

        self._value = UNKNOWN_VALUE

    @property
    def value(self):
        if self._value == UNKNOWN_VALUE:
            data = Fetcher().get_values(self._parent, self._name)


class StringField(BaseField):
    def __init__(self, *args, python_type=str, nullable=False, **kwargs):
        self.max_length = kwargs.pop("max_char")

        kwargs["python_type"] = python_type
        kwargs["nullable"] = nullable
        super().__init__(*args, **kwargs)


class IntegerField(BaseField):
    pass


class ForeignKeyField(BaseField):
    pass


FIELD_MAPPING = {str: StringField, int: IntegerField}
