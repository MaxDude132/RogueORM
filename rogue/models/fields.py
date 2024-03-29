from collections.abc import Iterable
from typing import get_args

from rogue.managers import RelationManager, ManyToManyManager
from rogue.query import InLookup, Lookup

from .errors import FieldValidationError
from .utils import get_through_model


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
        ), "Only union between a type and None is accepted."

        if args:
            type_ = [arg for arg in args if arg is not None][0]
        else:
            type_ = item

        return Field(type_, nullable=nullable)


class Field(metaclass=FieldMeta):
    def __init__(self, type_: type, nullable: bool = False):
        from .base import Model

        self.type: type = type_
        self.nullable: bool = nullable

        self._kwargs = {}

        if type_ not in FIELD_MAPPING and not issubclass(type_, Model):
            raise TypeError(f"{type_} is not supported.")

        if issubclass(type_, Model):
            self._field = ForeignKeyField
            self._kwargs["foreign_model_class"] = type_
        else:
            self._field = FIELD_MAPPING[self.type]

    def __call__(self, *args, **kwargs):
        nullable = kwargs.pop("nullable", False) or self.nullable

        # This is necessary to allow the following syntax in the model:
        #     field_name: Field[str](max_char=5)
        if not args:
            if self._field is ForeignKeyField and kwargs.get("one_to_one"):
                self._field = OneToOneField
            elif self._field is ForeignKeyField and kwargs.get("many_to_many"):
                self._field = ManyToManyField

            self._kwargs.update(kwargs)
            return self

        kwargs.update(self._kwargs)
        return self._field(*args, python_type=self.type, nullable=nullable, **kwargs)


class BaseField:
    PYTHON_TYPE = None

    def __init__(self, parent, field_name, python_type=None, nullable=False, **kwargs):
        self._parent = parent
        self.name = field_name
        self.python_type = python_type or self.PYTHON_TYPE
        self.nullable = nullable
        self.default = None
        self.is_pk = kwargs.get("primary_key", False)

    def validate(self, value):
        if value is None and not self.nullable and not self.is_pk:
            raise FieldValidationError(f"Field {self.name} cannot be None.")

        if value is not None and not isinstance(value, self.PYTHON_TYPE):
            raise FieldValidationError(
                f"Field {self.name} on model {self._parent.__name__} can only accept type {self.PYTHON_TYPE}, {type(value)} was passed."
            )

    def clean_value(self, value):
        if value is None and self.default:
            value = self.default

        return value

    def build_for_model(self, value):
        return value

    def get_relation_wrapper(self, field_name, value):
        return

    def available_lookups(self):
        return {"equal": Lookup, "in": InLookup}

    def get_query_table_name(self):
        return self._parent.table_name


class StringField(BaseField):
    PYTHON_TYPE = str

    def __init__(self, *args, **kwargs):
        self.max_char = kwargs.pop("max_char")
        super().__init__(*args, **kwargs)


class IntegerField(BaseField):
    PYTHON_TYPE = int


class FloatField(BaseField):
    PYTHON_TYPE = float


class RelationField(BaseField):
    pass


class BaseWrapper:
    pass


class ForeignKeyWrapper(BaseWrapper):
    def __init__(self, foreign_model, id):
        self._foreign_model = foreign_model
        self.id = id

        self._cache = None

    def __call__(self):
        if self.id is None:
            return None

        if self._cache is not None:
            return self._cache

        self._cache = self._foreign_model.get(id=self.id)
        return self._cache


class ForeignKeyField(RelationField):
    PYTHON_TYPE = int

    def __init__(self, parent, field_name, foreign_model_class, **kwargs):
        self._foreign_model = foreign_model_class
        self._model_field_name = field_name
        field_name = self._get_field_name()
        super().__init__(parent, field_name, **kwargs)

        reverse_relation_name = kwargs.get(
            "reverse_name", self._get_default_reverse_relation_name()
        )
        self._set_reverse_relation(reverse_relation_name)

    def _set_reverse_relation(self, reverse_relation_name):
        if hasattr(self._foreign_model, reverse_relation_name):
            raise FieldValidationError(
                f"{reverse_relation_name} already exists on the reverse relation for {self._model_field_name}. "
                "To fix this, set reverse_name on the field definition like so: Field[Model](reverse_name='my_reverse_name')"
            )

        setattr(
            self._foreign_model,
            reverse_relation_name,
            self._get_reverse_relation(self.name),
        )

    def _get_field_name(self):
        return self._model_field_name + "_id"

    def _get_default_reverse_relation_name(self):
        return self._parent.table_name + "_set"

    def _get_reverse_relation(self, field_name):
        return RelationManager(field_name, self._parent, self._parent)

    def clean_value(self, value):
        if value is not None and hasattr(value, "id") and hasattr(value, "save"):
            if value.id is None:
                value.save()

            value = value.id
        return super().clean_value(value)

    def get_relation_wrapper(self, field_name, value):
        return ForeignKeyWrapper(self._foreign_model, value)

    def available_lookups(self):
        model_lookups = super().available_lookups()

        return {**model_lookups, **self._foreign_model.available_lookups()}


class OneToOneWrapper(BaseWrapper):
    def __init__(self, foreign_model):
        self._foreign_model = foreign_model
        self._cache = None
        self.id = None

    def __call__(self):
        if self.id is None:
            return None

        if self._cache is not None:
            return self._cache

        self._cache = self._foreign_model.get(id=self.id)
        return self._cache


class OneToOneField(ForeignKeyField):
    def _get_default_reverse_relation_name(self):
        return self._parent.table_name

    def _get_reverse_relation(self, _field_name):
        return OneToOneWrapper(self._parent)


class ManyToManyField(ForeignKeyField):
    PYTHON_TYPE = Iterable

    def __init__(self, parent, field_name, foreign_model_class, **kwargs):
        nullable = kwargs.get("nullable", False)
        # kwargs["nullable"] = True
        super().__init__(parent, field_name, foreign_model_class, **kwargs)

        self.reverse_name = kwargs.get(
            "reverse_name", self._get_default_reverse_relation_name()
        )

        self._through_model = kwargs.get(
            "through",
            get_through_model(
                parent,
                foreign_model_class,
                self._get_field_name(),
                self.reverse_name,
                nullable,
            ),
        )

        self._mapping = {
            self._get_field_name(): self.reverse_name,
            self.reverse_name: self._get_field_name(),
        }

    def _set_reverse_relation(self, reverse_relation_name):
        return

    def _get_field_name(self):
        return self._model_field_name

    def get_relation_wrapper(self, field_name, value):
        return ManyToManyManager(self._through_model, self._foreign_model)

    def clean_value(self, value):
        if value is None:
            return

        if not isinstance(value, Iterable):
            value = [value]

        return value

    def get_query_table_name(self):
        return self._foreign_model.table_name


FIELD_MAPPING = {str: StringField, int: IntegerField, float: FloatField}
