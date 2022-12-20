from rogue.backends.sqlite.client import DatabaseClient
from rogue.backends.sqlite.query import QueryBuilder

from .errors import ExecutionError


class Manager:
    def __init__(self, model):
        self.model = model

        self._client = DatabaseClient(self.model.db_name)
        self._query = QueryBuilder(self._client, model)
        self._method = None
        self._cache = None

    def first(self):
        return self._build_models(self._query.fetch_one())

    def all(self):
        self._method = self._query.fetch_all
        return self

    def where(self, **where):
        where = self._deconstruct_where(where)
        if where:
            for lookup, comparison, value in where:
                self._query = self._query.where(lookup, comparison, value)
        return self

    def insert(self, data):
        return self._query.insert(data)[0]

    def update(self, pk, data):
        pass

    def _deconstruct_where(self, where):
        formatted_where = []

        for lookup, value in where.items():
            formatted_where.append((lookup, "=", value))

        return formatted_where

    def _build_models(self, data):
        models = []
        for row in data:
            models.append(self.model(**row))

        return models

    def __iter__(self):
        if self._method is None:
            raise ExecutionError("Cannot iterate over nothing.")

        if self._cache:
            data = self._cache
        else:
            data = self._method()
            data = self._build_models(data)
            self._cache = data

        return iter(data)
