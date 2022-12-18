from typing import Any
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

        if not (__annotations__ := namespace.get("__annotations__")):
            return instance

        pk_fields = []
        for name, obj in __annotations__.items():
            if obj is Field:
                raise TypeError(
                    "Field must be used with type hinting. For example, call it like so: Field[str]."
                )
            if isinstance(obj, Field):
                obj = obj()
            if isinstance(obj, BaseField) and name in namespace:
                obj.default = namespace[name]
            setattr(instance, name, obj)

            if obj.is_pk:
                pk_fields.append(obj)

        if not pk_fields:
            instance.id = IntegerField(primary_key=True)

        return instance


class Model(metaclass=ModelMeta):
    @property
    def fields(self):
        return {
            field_name: field
            for field_name, field in self.__class__.__dict__.items()
            if isinstance(field, BaseField)
        }
