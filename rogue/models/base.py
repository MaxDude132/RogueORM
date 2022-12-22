from typing import Any, get_args
import re

from rogue.managers import Manager

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
        self._foreign_relations = {}

        for field_name, field in self.get_model_fields().items():
            value = field.clean_value(kwargs.get(field_name))
            value = field.build_for_model(value)
            field.validate(value)

            if field.name:
                setattr(self, field.name, value)

            foreign_relations = field.foreign_relations(value)
            if foreign_relations:
                self._foreign_relations[field_name] = foreign_relations

        self.__values_last_save = self.field_values

    @classmethod
    def _get_new_manager(cls):
        return Manager(cls)

    def save(self):
        created = False
        manager = self._get_new_manager()
        field_values = self.field_values

        if self.id is None:
            created = True
            del field_values["id"]
            new_values = manager.insert(field_values)
            self.id = new_values["id"]
            self.__values_last_save["id"] = self.id
        else:
            manager.update(self.id, self.get_changed_fields())

        if not created:
            for field_name, value in field_values.items():
                setattr(self, field_name, value)
                self.__values_last_save[field_name] = value

        return created

    def delete(self):
        self._get_new_manager().delete(self.id)
        self.id = None

    @classmethod
    def get(cls, **kwargs):
        return cls._get_new_manager().where(**kwargs).first()

    @classmethod
    def where(cls, **kwargs):
        return cls._get_new_manager().where(**kwargs)

    @classmethod
    def where_not(cls, **kwargs):
        return cls._get_new_manager().where_not(**kwargs)

    @classmethod
    def all(cls):
        return cls._get_new_manager().all()

    @classmethod
    def get_fields(cls):
        return {
            field.name: field
            for field in cls.__dict__.values()
            if isinstance(field, BaseField) and field.name
        }

    @classmethod
    def get_model_fields(cls):
        return {
            field_name: field
            for field_name, field in cls.__dict__.items()
            if isinstance(field, BaseField)
        }

    @classmethod
    def get_field_names(cls):
        return [
            field.name
            for field in cls.__dict__.values()
            if isinstance(field, BaseField)
        ]

    @property
    def field_values(self):
        return {
            field.name: getattr(self, field_name)
            for field_name, field in self.get_fields().items()
            if field.name
        }

    def get_changed_fields(self):
        changed_fields = {}

        for field, value in self.field_values.items():
            if value != self.__values_last_save.get(field):
                changed_fields[field] = value

        return changed_fields

    def __setattr__(self, attr, value):
        fields = self.get_fields()

        if attr in fields:
            fields[attr].validate(value)

        super().__setattr__(attr, value)

    def __getattribute__(self, name: str):
        if name != "_foreign_relations" and name in getattr(
            self, "_foreign_relations", []
        ):
            return self._foreign_relations[name]()

        return super().__getattribute__(name)

    def __repr__(self) -> str:
        fields = [
            f"{str(field)}={str(value)}" for field, value in self.field_values.items()
        ]
        return f"<{self.__class__.__name__} {', '.join(fields)}>"
