from typing import Any
import re

from rogue.models.errors import NotAKnownField
from .fields import BaseField, Field, IntegerField


class ModelMeta(type):
    def __new__(
        cls: type,
        name: str,
        bases: tuple[type, ...],
        namespace: dict[str, Any],
        **kwds: Any,
    ):
        instance = super().__new__(cls, name, bases, namespace, **kwds)

        if name == "Model":
            return instance

        instance.table_name = cls._get_table_name(name)

        instance.id = Field[int](instance, name, primary_key=True)

        __annotations__ = namespace.get("__annotations__") or {}

        for name, obj in __annotations__.items():
            if obj is Field:
                raise TypeError(
                    "Field must be used with type hinting. For example, call it like so: Field[str]."
                )
            if isinstance(obj, Field):
                obj = obj(instance, name)
            if isinstance(obj, BaseField) and name in namespace:
                obj.default = namespace[name]
            setattr(instance, name, obj)

        return instance

    @classmethod
    def _get_table_name(cls, name):
        return "_".join(re.sub(r"([A-Z])", r" \1", name).split()).lower()


class Model(metaclass=ModelMeta):
    def __init__(self, **kwargs):
        self.table_name = None

        for field_name, field in self.fields.items():
            if field_name in kwargs:
                field.value = kwargs[field_name]

    @classmethod
    def get_fields(cls):
        return {
            field_name: field
            for field_name, field in cls.__dict__.items()
            if isinstance(field, BaseField)
        }

    @property
    def fields(self):
        return self.get_fields()

    def _get_field_value(self, field_name):
        try:
            self.__class__.__dict__.get(field_name).value
        except AttributeError:
            raise NotAKnownField()

    def __getattribute__(self, __name: str) -> Any:
        if __name in ("__class__", "fields", "get_fields"):
            return super().__getattribute__(__name)
        elif __name in (fields := self.get_fields()):
            return fields[__name].value

        return super().__getattribute__(__name)

    def __str__(self) -> str:
        return f"<{self.__class__.__name__} {', '.join([f'{name}={field.value}' for name, field in self.fields.items()])}>"
