from copy import copy
from typing import Any
import re

from rogue.managers import Manager, RelationManager, ManyToManyManager
from rogue.settings import settings

from .fields import (
    BaseField,
    Field,
    RelationField,
    OneToOneWrapper,
    BaseWrapper,
    ManyToManyField,
)


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
    db_name = settings.DATABASE_NAME

    def __init__(self, **kwargs):
        self._foreign_relations = {}

        id_ = kwargs.get("id")

        self._set_related_managers()
        self._set_related_managers_id(id_)

        for field_name, field in self.get_model_fields().items():
            value = field.clean_value(kwargs.pop(field_name, None))
            value = field.build_for_model(value)
            field.validate(value)

            if field.name:
                setattr(self, field.name, value)

            foreign_relations = field.get_relation_wrapper(field.name, value)
            if isinstance(foreign_relations, ManyToManyManager):
                foreign_relations.id = id_
                foreign_relations.lookup_field = self.table_name + "_id"
            if foreign_relations is not None:
                self._foreign_relations[field_name] = foreign_relations

        for attr, value in kwargs.items():
            setattr(self, attr, value)

        self.__values_last_save = self.field_values

    def _set_related_managers(self):
        for field, manager in self.get_class_related_managers().items():
            setattr(self, field, copy(manager))

    def _set_related_managers_id(self, id):
        for manager in self.get_related_managers().values():
            manager.id = id

        for manager in self.get_many_managers().values():
            manager.id = id

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
            self._set_related_managers_id(self.id)
        else:
            manager.update(self.id, self.get_changed_fields())

        if created:
            for field_name, field in self.get_many_managers().items():
                if field_name in self.__dict__:
                    value = self.__dict__.get(field_name)
                    if value is not None:
                        field.add(value)

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
    def none(cls):
        return cls._get_new_manager().none()

    @classmethod
    def get_fields(cls):
        return {
            field.name: field
            for field in cls.__dict__.values()
            if isinstance(field, BaseField)
            and field.name
            and not isinstance(field, ManyToManyField)
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
        return list(cls.get_fields())

    @classmethod
    def get_related_fields(cls):
        return {
            field_name: field
            for field_name, field in cls.get_model_fields().items()
            if isinstance(field, RelationField)
        }

    @classmethod
    def get_class_related_managers(cls):
        return {
            field_name: field
            for field_name, field in cls.__dict__.items()
            if isinstance(field, (RelationManager, OneToOneWrapper))
        }

    def get_related_managers(self):
        return {
            field_name: field
            for field_name, field in self.__dict__.items()
            if isinstance(field, (RelationManager, OneToOneWrapper))
        }

    def get_many_managers(self):
        return {
            field_name: field
            for field_name, field in self.__dict__.get("_foreign_relations", {}).items()
            if isinstance(field, ManyToManyManager)
        }

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
        attribute = super().__getattribute__(name)

        if name != "_foreign_relations" and name in getattr(
            self, "_foreign_relations", []
        ):
            attribute = self._foreign_relations[name]

        if isinstance(attribute, BaseWrapper):
            return attribute()

        return attribute

    def __eq__(self, obj: object) -> bool:
        return isinstance(obj, self.__class__) and obj.id == self.id

    def __repr__(self) -> str:
        fields = [
            f"{str(field)}={str(value)}" for field, value in self.field_values.items()
        ]
        return f"<{self.__class__.__name__} {', '.join(fields)}>"
