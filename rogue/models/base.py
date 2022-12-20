from typing import Any
import re

from rogue.managers import Manager

from .errors import MissingFieldValueError
from .fields import BaseField, Field


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
        instance.id = Field[int](instance, "id", primary_key=True)

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
    db_name = "default.sqlite"

    def __init__(self, **kwargs):
        self._instantiate_fields()

        for field_name, field in self.fields.items():
            if field_name in kwargs:
                field.value = kwargs[field_name]
            elif field.nullable:
                field.value = None
            elif not field.is_pk:
                raise MissingFieldValueError(f"Field {field_name} cannot be None.")

    def _instantiate_fields(self):
        for field_name, field in self.get_class_fields().items():
            setattr(self, field_name, field())

    @classmethod
    def _get_new_manager(cls):
        return Manager(cls)

    def save(self):
        manager = self._get_new_manager()
        all_field_values = self.get_all_field_values()

        if self.id is None:
            del all_field_values["id"]
            new_values = manager.insert(all_field_values)
            self.id = new_values["id"]
        else:
            manager.update(self.get_all_field_values())

    @classmethod
    def get(cls, **kwargs):
        try:
            return cls._get_new_manager().where(**kwargs).first()[0]
        except IndexError:
            return None

    @classmethod
    def all(cls):
        return cls._get_new_manager().all()

    @classmethod
    def get_class_fields(cls):
        return {
            field_name: field
            for field_name, field in cls.__dict__.items()
            if isinstance(field, BaseField)
        }

    @property
    def fields(self):
        return {
            field_name: field
            for field_name, field in self.__dict__.items()
            if isinstance(field, BaseField)
        }

    def get_all_field_values(self):
        return {field_name: field.value for field_name, field in self.fields.items()}

    def __getattribute__(self, __name: str) -> Any:
        if __name in (
            "__class__",
            "__dict__",
            "get_class_fields",
            "fields",
        ):
            return super().__getattribute__(__name)
        elif __name in (fields := self.fields):
            return fields[__name].value

        return super().__getattribute__(__name)

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} {', '.join([str(field) for field in self.fields.values()])}>"
