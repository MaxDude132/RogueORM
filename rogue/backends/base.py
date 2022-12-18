from abc import ABCMeta, abstractmethod
from dataclasses import dataclass
from typing import Any

from rogue.backends.errors import FormatAlreadyDefined, FormatNotRecognized


class BaseDatabaseClient(metaclass=ABCMeta):
    _instances = {}
    _db_name = None

    def __new__(cls, db_name):
        if db_name not in cls._instances:
            cls._instances[db_name] = super().__new__(cls)

        return cls._instances[db_name]

    def __init__(self, db_name):
        self._db_name = db_name

        self._connection = None

    @abstractmethod
    def get_connection(self):
        pass

    @abstractmethod
    def execute(self, statement, *args, **kwargs):
        pass

    @abstractmethod
    def close(self):
        pass


@dataclass
class WhereStatement:
    field: str
    comparison: str
    value: Any


class BaseQueryBuilder(metaclass=ABCMeta):
    SELECT = "SELECT"
    UPDATE = "UPDATE"
    INSERT = "INSERT"
    AVAILABLE_FORMATS = (SELECT, UPDATE, INSERT)

    FROM = "FROM"
    WHERE = "WHERE"
    AND = "AND"

    def __init__(self, client):
        self.client = client
        self.format = None

        self.table_name = None
        self.where_statements = []

    def set_query_format(self, format):
        if self.format:
            raise FormatAlreadyDefined()

        if format not in self.AVAILABLE_FORMATS:
            raise FormatNotRecognized()

        self.format = format

    def _query_start(self, model):
        self.table_name = model.table_name
        self.fields = model.get_fields()

    def select_from(self, model):
        self._query_start(model)

        self.set_query_format(self.SELECT)
        return self

    def where(self, field, comparison, value):
        self.where_statements.append(
            WhereStatement(field=field, comparison=comparison, value=value)
        )
        return self

    def _build_query(self):
        if self.format == self.SELECT:
            return self._build_select()

    @abstractmethod
    def _build_select(self):
        pass

    @abstractmethod
    def _build_where(self):
        pass


class BaseDatabaseSchemaEditor(metaclass=ABCMeta):
    pass
