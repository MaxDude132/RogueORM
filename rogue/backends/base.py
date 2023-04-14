from abc import ABCMeta, abstractmethod
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any

from rogue.settings import settings

from .errors import OperationalError, InvalidComparisonError


class BaseDatabaseClient(metaclass=ABCMeta):
    _instances = {}
    _db_name = None

    def __new__(cls, db_name=settings.DATABASE_NAME):
        if db_name not in cls._instances:
            cls._instances[db_name] = super().__new__(cls)

        return cls._instances[db_name]

    def __init__(self, db_name=settings.DATABASE_NAME):
        self._db_name = db_name

        self._connection = None

    @abstractmethod
    def get_connection(self):  # pragma: no cover
        pass

    @abstractmethod
    def execute(self, statement, *args, **kwargs):  # pragma: no cover
        pass

    @abstractmethod
    def close(self):  # pragma: no cover
        pass


@dataclass
class WhereStatement:
    table_name: str
    field: str
    comparison: str
    value: Any
    relation_descriptor: Any


class BaseQueryBuilder(metaclass=ABCMeta):
    SELECT = "SELECT"
    UPDATE = "UPDATE"
    INSERT = "INSERT INTO"
    DELETE = "DELETE"

    FROM = "FROM"
    WHERE = "WHERE"
    AND = "AND"
    VALUES = "VALUES"
    INNER_JOIN = "INNER JOIN"
    ON = "ON"

    EQUAL = "equal"
    IN = "in"

    COMPARISON_MAPPING = {
        EQUAL: "=",
        IN: "IN",
    }
    NOT_COMPARISON_MAPPING = {
        EQUAL: "!=",
        IN: "NOT IN",
    }

    COMPARISON_DEFAULT = EQUAL

    def __init__(self, client, model):
        self.client = client
        self.model = model

        self.where_statements = []

    @property
    def table_name(self):
        return self.model.table_name

    @property
    def fields(self):
        return self.model.get_fields()

    def where(
        self,
        *,
        table_name,
        field,
        comparison,
        value,
        not_: bool = False,
        relation_descriptor=None,
    ):
        comparison_mapping = (
            self.NOT_COMPARISON_MAPPING if not_ else self.COMPARISON_MAPPING
        )

        if not comparison:
            comparison = self.COMPARISON_DEFAULT

        try:
            comparison = comparison_mapping[comparison]
        except KeyError:
            raise InvalidComparisonError(
                f"{comparison} is not a valid comparison operator."
            )

        self.where_statements.append(
            WhereStatement(
                table_name=table_name,
                field=field,
                comparison=comparison,
                value=value,
                relation_descriptor=relation_descriptor,
            )
        )
        return self

    @abstractmethod
    def fetch_one(self):  # pragma: no cover
        pass

    @abstractmethod
    def fetch_all(self):  # pragma: no cover
        pass

    @abstractmethod
    def insert(self, data):  # pragma: no cover
        pass

    @abstractmethod
    def update(self, pk, data):  # pragma: no cover
        pass

    @abstractmethod
    def delete(self, pk):  # pragma: no cover
        pass

    def _format_input_row(self, headers, data):
        headers = list(data)
        formatted_data = [data[header] for header in headers]
        return formatted_data

    def _format_input_data(self, data):
        if isinstance(data, dict):
            headers = list(data)
            formatted_data = self._format_input_row(headers, data)

        return headers, formatted_data

    def _format_output_data(self, data):
        assert isinstance(data, Iterable), "Field data must be an iterable."

        formatted_data = []

        if not data or data[0] is None:
            return formatted_data

        for row in data:
            formatted_data.append(dict(zip(self.fields.keys(), row)))

        return formatted_data

    @abstractmethod
    def _build_select(self):  # pragma: no cover
        pass

    @abstractmethod
    def _build_insert(self, data):  # pragma: no cover
        pass

    @abstractmethod
    def _build_update(self, pk, data):  # pragma: no cover
        pass

    @abstractmethod
    def _build_delete(self, pk):  # pragma: no cover
        pass

    @abstractmethod
    def _build_where(self):  # pragma: no cover
        pass

    def _validate_data(self, data):
        assert data is not None, "Cannot insert without data."


class BaseDatabaseSchemaEditor(metaclass=ABCMeta):
    def __init__(self, db_client: BaseDatabaseClient) -> None:
        self._db_client = db_client


class BaseDatabaseSchemaReader(metaclass=ABCMeta):
    def __init__(self, db_client: BaseDatabaseClient) -> None:
        self._db_client = db_client

    @abstractmethod
    def get_tables(self):  # pragma: no cover
        pass

    @abstractmethod
    def get_rows(self, table_name):  # pragma: no cover
        pass
