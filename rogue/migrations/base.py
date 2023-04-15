from rogue.backends.sqlite.client import DatabaseClient
from rogue.backends.sqlite.schema import DatabaseSchemaEditor, DatabaseSchemaReader
from rogue.models.utils import get_all_models
from rogue.settings import settings


def makemigrations(db_name=None):
    db_name = db_name or settings.DATABASE_NAME

    migrator = MigrationCreator(db_name=db_name)
    migration_name = migrator.create_migration()

    print(f"Migration {migration_name} created!")
    return migration_name


def migrate(filename, db_name=None):
    if filename is None:
        raise ValueError(
            "A value must be passed for filename when running the migrate command."
        )

    db_name = db_name or settings.DATABASE_NAME
    db_client = DatabaseClient(db_name)

    with open(filename) as file:
        for statement in file.read().split(";"):
            print(statement)
            db_client.execute(statement)
            print("Successful!")


class MigrationCreator:
    def __init__(self, db_name) -> None:
        self.db_name = db_name
        self._db_client = DatabaseClient(self.db_name)
        self._schema_reader = DatabaseSchemaReader(self._db_client)
        self._schema_editor = DatabaseSchemaEditor(self._db_client)

    def create_migration(self):
        diff = self.process_differences()
        sql = self._schema_editor.build_sql_migration(diff)
        migration_name = self.get_migration_name()

        with open(migration_name, "w") as file:
            file.write(sql)

        return migration_name

    def get_migration_name(self):
        # TODO: Add a way to keep track of migration names
        return "migration.sql"

    def process_differences(self):
        current_database_schema = self.analyze_database()
        new_database_schema = self.models_schema()

        tables_to_create = {}
        tables_to_modify = {}
        tables_to_delete = []

        for table_name, rows in new_database_schema.items():
            if table_name not in current_database_schema:
                tables_to_create[table_name] = rows
                continue

            if rows != current_database_schema[table_name]:
                changes = self._get_rows_diff(current_database_schema[table_name], rows)
                tables_to_modify[table_name] = changes

        for table_name in current_database_schema:
            if table_name not in new_database_schema:
                tables_to_delete.append(table_name)

        return {
            "create": tables_to_create,
            "alter": tables_to_modify,
            "delete": tables_to_delete,
        }

    def analyze_database(self):
        schema = {}

        tables = self._schema_reader.get_tables()
        for table in tables:
            schema[table] = self._schema_reader.get_rows(table)

        return schema

    def models_schema(self):
        schema = {}

        all_models = get_all_models()
        for model in all_models:
            rows = []
            for row in model.get_model_fields().values():
                # TODO: Make smarter, and based on the database backend used
                row_type = "integer" if row.PYTHON_TYPE is int else "text"
                rows.append(
                    {
                        "name": row.name,
                        "type": row_type,
                        "notnull": not row.nullable,
                        "default_value": row.default,
                        "is_pk": row.is_pk,
                    }
                )

            schema[model.table_name] = rows

        return schema

    def _get_rows_diff(self, old_rows, new_rows):
        create = []
        alter = []
        delete = []
        no_change = []

        old_rows = {row["name"]: row for row in old_rows}
        new_rows = {row["name"]: row for row in new_rows}

        for name in old_rows:
            if name not in new_rows:
                delete.append(name)

        for name, row in new_rows.items():
            if name not in old_rows:
                create.append(row)
                continue

            if row != old_rows[name]:
                alter.append(row)
            else:
                no_change.append(row)

        return {
            "create": create,
            "alter": alter,
            "delete": delete,
            "no_change": no_change,
        }
