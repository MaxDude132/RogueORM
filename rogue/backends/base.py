from abc import ABCMeta, abstractmethod
from dataclasses import dataclass
from typing import Any

from rogue.backends.errors import FormatNotRecognized


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
    INSERT = "INSERT INTO"
    AVAILABLE_FORMATS = (SELECT, UPDATE, INSERT)

    FROM = "FROM"
    WHERE = "WHERE"
    AND = "AND"
    VALUES = "VALUES"

    def __init__(self, client, model):
        self.client = client
        self.model = model

        self.table_name = self.model.table_name
        self.fields = self.model.get_class_fields()

        self.where_statements = []

        self.format = format

    def where(self, field, comparison, value):
        self.where_statements.append(
            WhereStatement(field=field, comparison=comparison, value=value)
        )
        return self

    @abstractmethod
    def fetch_one(self):
        pass

    @abstractmethod
    def fetch_many(self, limit=None):
        pass

    @abstractmethod
    def fetch_all(self):
        pass

    def _format_data(self, data):
        formatted_data = []

        for row in data:
            formatted_data.append(dict(zip(self.fields.keys(), row)))

        return formatted_data

    def _build_query(self, format_, data=None):
        if format_ not in self.AVAILABLE_FORMATS:
            raise FormatNotRecognized(
                f"Format {format_} is not an available format. Available formats are: {', '.join(self.AVAILABLE_FORMATS)}"
            )

        if format_ == self.SELECT:
            return self._build_select()
        elif format_ == self.INSERT:
            return self._build_insert(data)

    @abstractmethod
    def _build_select(self):
        pass

    @abstractmethod
    def _build_insert(self):
        pass

    @abstractmethod
    def _build_where(self):
        pass


class BaseDatabaseSchemaEditor(metaclass=ABCMeta):
    pass
