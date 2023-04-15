from collections.abc import Iterable

from rogue.backends.sqlite.client import DatabaseClient
from rogue.backends.sqlite.query import QueryBuilder
from rogue.models.query import Lookup

from .errors import ManagerValidationError
from .query import RelationDescriptor


LOOKUP_SEPARATOR = "__"


class Manager:
    def __init__(self, model_class, parent=None):
        self.model_class = model_class
        self._parent = None

        self._client = DatabaseClient(self.model_class.db_name)
        self._query = QueryBuilder(self._client, self.model_class)
        self._cache = None
        self._is_none = False

        self._joins = {}

    def first(self):
        if self._is_none:
            return

        self._base_filtering()

        data = self._build_models(self._query.fetch_one())
        try:
            return data[0]
        except (IndexError, TypeError):
            return

    def all(self):
        return self

    def where(self, not_=False, table_name=None, **where):
        where = self._deconstruct_where(where)
        if where:
            # TODO: Filter the data instead of forcing a refetch
            self._cache = None
            for lookup in where:
                relation_descriptor = (
                    RelationDescriptor(*lookup.tracking)
                    if len(lookup.tracking) > 1
                    else None
                )
                self._query = self._query.where(
                    table_name=table_name or lookup.parent.get_query_table_name(),
                    field=lookup.parent.name,
                    comparison=lookup.comparison,
                    value=lookup.value,
                    not_=not_,
                    relation_descriptor=relation_descriptor,
                )
        return self

    def where_not(self, **where):
        return self.where(not_=True, **where)

    def insert(self, data):
        self.validate_data(data)
        return self._query.insert(data)[0]

    def update(self, pk, data):
        self.validate_data(data)
        return self._query.update(pk, data)[0]

    def delete(self, pk):
        self.where(id=pk)._query.delete()

    def none(self):
        self._is_none = True
        return self

    def validate_data(self, data):
        if data is None:
            raise ManagerValidationError(
                "The data argument must be passed for insert or update."
            )

        model_fields = self.model_class.get_fields()

        for field_name in data:
            if field_name not in self.model_class.get_field_names():
                raise ManagerValidationError(
                    f"{self.model_class.table_name} has no field named {field_name}."
                )
            model_fields[field_name].validate(data[field_name])

    def available_lookups(self):
        return self.model_class.available_lookups()

    def _deconstruct_where(self, where):
        formatted_where = []

        for lookup_str, value in where.items():
            lookup = self._get_lookup_object(lookup_str, value)
            formatted_where.append(lookup)

        return formatted_where

    def _get_lookup_object(self, lookup: str, value):
        available_lookups = self.available_lookups()
        prev_obj = None
        obj = None

        tracking = []
        for item in lookup.split(LOOKUP_SEPARATOR):
            try:
                prev_obj = obj
                obj = available_lookups[item]
                tracking.append(obj)
            except KeyError:
                raise LookupError(
                    f"{item} is not a valid lookup. Options are {', '.join(available_lookups)}."
                )

            if not hasattr(obj, "available_lookups"):
                break

            available_lookups = obj.available_lookups()

        if isinstance(obj, type) and issubclass(obj, Lookup):
            return obj(prev_obj, value, tracking)

        return Lookup(obj, value, tracking)

    def _build_models(self, data):
        models = []
        for row in data:
            row = self._build_relations(row)
            model_class = self.get_returned_model_class()
            models.append(model_class(id_=row.get("id"), parent=self, **row))

        return models

    def _build_relations(self, row):
        for field_name, field in self.model_class.get_related_fields().items():
            if field.name in row:
                row[field_name] = row[field.name]
            elif hasattr(field, "_through_model"):
                relation_manager = field.get_relation_wrapper(field_name, None)
                relation_manager.id = row.get("id")
                row[field_name] = relation_manager
        return row

    def get_returned_model_class(self):
        return self.model_class

    def get_query_table_name(self):
        return self.model_class.table_name

    def __iter__(self):
        return iter(self.all_models)

    @property
    def all_data(self):
        obj = self._base_filtering()

        if self._is_none or self.model_class.get_field_names() == ["id"]:
            return []

        if obj._cache is not None:
            data = obj._cache
        else:
            data = obj._query.fetch_all()
            obj._cache = data

        return data

    def _base_filtering(self):
        return self

    @property
    def all_models(self):
        return self._build_models(self.all_data)

    def __eq__(self, other):
        return self.all_data == other.all_data

    def __len__(self):
        return len(list(self.__iter__()))

    def __contains__(self, other):
        if not isinstance(other, self.model_class):
            return False

        for data in self.all_data:
            if other.id == data["id"]:
                return True

        return False

    def __repr__(self):
        return f"<{self.__class__.__name__} [{', '.join(str(model) for model in self.all_models)}]>"


class RelationManager(Manager):
    def __init__(self, lookup_field, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.lookup_field = lookup_field
        self.id = None

    def _base_filtering(self):
        if self.id is None:
            return self.none()

        return self.where(**{self.lookup_field: self.id})


class ManyToManyManager(Manager):
    def __init__(self, through_model, relation_model):
        super().__init__(through_model)
        self.lookup_field = None
        self.id = None

        self.relation_model = relation_model

    def _base_filtering(self):
        if self.id is None:
            return self.none()

        self._query.model = self.relation_model
        return self.where(table_name=self.get_query_table_name(), id=self.id)

    def add(self, data):
        # TODO: Add a way to insert many with one query
        if isinstance(data, Iterable):
            all_data = []
            for row in data:
                insert_data = self._get_ids_from_row(row)
                all_data.append(self.insert(insert_data))
            return all_data

        insert_data = self._get_ids_from_row(data)
        return self.insert(insert_data)

    def _get_ids_from_row(self, row):
        if not row:
            return {}

        return {row.table_name + "_id": row.id, self.lookup_field: self.id}

    def get_returned_model_class(self):
        return self.relation_model

    def get_query_table_name(self):
        return self.relation_model.table_name
