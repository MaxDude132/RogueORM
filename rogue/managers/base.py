from rogue.backends.sqlite.client import DatabaseClient
from rogue.backends.sqlite.query import QueryBuilder

from .errors import ManagerValidationError


LOOKUP_SEPARATOR = "__"


class Manager:
    def __init__(self, model):
        self.model = model

        self._client = DatabaseClient(self.model.db_name)
        self._query = QueryBuilder(self._client, model)
        self._cache = None

    def first(self):
        try:
            return self._build_models(self._query.fetch_one())[0]
        except (IndexError, TypeError):
            return

    def all(self):
        return self

    def where(self, not_=False, **where):
        where = self._deconstruct_where(where)
        if where:
            # TODO: Filter the data instead of forcing a refetch
            self._cache = None
            for lookup, comparison, value in where:
                self._query = self._query.where(lookup, comparison, value, not_)
        return self

    def where_not(self, **where):
        return self.where(not_=True, **where)

    def insert(self, data):
        self.validate_data(data)
        return self._query.insert(data)[0]

    def update(self, pk, data):
        self.validate_data(data)
        return self._query.update(pk, data)[0]

    def validate_data(self, data):
        if not data:
            raise ManagerValidationError(
                "The data argument must be passed for insert or update."
            )

        model_fields = self.model.get_fields()

        for field_name in data:
            if field_name not in self.model.get_fields():
                raise ManagerValidationError(
                    f"{self.model.table_name} has no field named {field_name}."
                )
            model_fields[field_name].validate(data[field_name])

    def _deconstruct_where(self, where):
        formatted_where = []

        for lookup, value in where.items():
            comparison = ""

            if LOOKUP_SEPARATOR in lookup:
                lookup, comparison = lookup.split(LOOKUP_SEPARATOR)

            formatted_where.append((lookup, comparison, value))

        return formatted_where

    def _build_models(self, data):
        models = []
        for row in data:
            models.append(self.model(**row))

        return models

    def __iter__(self):
        return iter(self.all_models)

    @property
    def all_data(self):
        if self._cache:
            data = self._cache
        else:
            data = self._query.fetch_all()
            self._cache = data

        return data

    @property
    def all_models(self):
        return self._build_models(self.all_data)

    def __eq__(self, other):
        return self.all_data == other.all_data

    def __len__(self):
        return len(list(self.__iter__()))

    def __repr__(self):
        return f"<{self.__class__.__name__} [{', '.join(str(model) for model in self.all_models)}]>"
