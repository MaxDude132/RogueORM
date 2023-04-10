from .client import DatabaseClient
from ..base import BaseDatabaseSchemaEditor, BaseDatabaseSchemaReader


class DatabaseSchemaEditor(BaseDatabaseSchemaEditor):
    pass


class DatabaseSchemaReader(BaseDatabaseSchemaReader):
    def __init__(self, db_client: DatabaseClient) -> None:
        super().__init__(db_client)

    def get_tables(self):
        tables = self._db_client.execute(
            "SELECT name FROM sqlite_schema WHERE type='table' AND name NOT LIKE 'sqlite_%';"
        ).fetchall()
        return [table[0] for table in tables]

    def get_rows(self, table_name):
        rows = self._db_client.execute(f"PRAGMA table_info({table_name});").fetchall()

        formatted_rows = []
        for row in rows:
            formatted_rows.append(
                {
                    "cid": row[0],
                    "name": row[1],
                    "type": row[2],
                    "notnull": bool(row[3]),
                    "dflt_value": row[4],
                    "pk": bool(row[5]),
                }
            )

        return formatted_rows
