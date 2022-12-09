from typing import get_args


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
        from .base import Model # TODO: Find a way to avoid this import

        self.type: type = type_
        self.nullable: bool = nullable

        if issubclass(type_, Model):
            self._field = ForeignKeyField
        elif type_ not in FIELD_MAPPING:
            raise TypeError(f"{type_} is not supported.")
        else:
            self._field = FIELD_MAPPING[self.type]

    def __call__(self, **kwargs):
        return self._field(
            python_type=self.type, nullable=self.nullable, **kwargs
        )


class BaseField:
    def __init__(self, python_type=int, nullable=False, **kwargs):
        self.python_type = python_type
        self.nullable = nullable
        self.is_pk = kwargs.get("primary_key", False)


class StringField(BaseField):
    def __init__(self, python_type=str, nullable=False, **kwargs):
        super().__init__(python_type=python_type, nullable=nullable)
        self.max_length = kwargs.get("max_char")


class IntegerField(BaseField):
    pass


class ForeignKeyField(BaseField):
    pass


FIELD_MAPPING = {str: StringField, int: IntegerField}
