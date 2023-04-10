from rogue.backends.sqlite.client import DatabaseClient
from rogue.backends.sqlite.schema import DatabaseSchemaReader


def makemigrations():
    db_name = "default.sqlite"

    migrator = Migrator(db_name=db_name)
    print(migrator.process_differences())


class Migrator:
    def __init__(self, db_name) -> None:
        self.db_name = db_name
        self._db_client = DatabaseClient(self.db_name)
        self._schema_reader = DatabaseSchemaReader(self._db_client)

    def process_differences(self):
        current_database_schema = self.analyze_database()
        new_database_schema = self.models_schema()

        return current_database_schema

    def analyze_database(self):
        schema = {}

        tables = self._schema_reader.get_tables()
        for table in tables:
            schema[table] = self._schema_reader.get_rows(table)

        return schema

    def models_schema(self):
        pass
