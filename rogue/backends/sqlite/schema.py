import sqlparse
from ..base import BaseDatabaseSchemaEditor, BaseDatabaseSchemaReader


DEFAULT_VALUE = "default_value"


class DatabaseSchemaEditor(BaseDatabaseSchemaEditor):
    def build_sql_migration(self, diff):
        statements = []

        statements.extend(self._build_delete_statements(diff["delete"]))
        statements.extend(self._build_alter_statements(diff["alter"]))
        statements.extend(self._build_create_statements(diff["create"]))

        sql = sqlparse.format(
            "".join(statements),
            keyword_case="upper",
            identifier_case="lower",
            reindent=True,
        )
        return sql

    def _build_delete_statements(self, diff):
        statements = []

        for table_name in diff:
            statements.append(f"DROP TABLE {table_name};")

        return statements

    def _build_alter_statements(self, diff):
        statements = []

        for table_name, changes in diff.items():
            if not changes["alter"] and not changes["delete"]:
                for row in changes["create"]:
                    statement = f"ALTER TABLE {table_name} ADD "
                    statement += self._format_column(row, add_comma=False)
                    statement += ";"
                    statements.append(statement)

            else:
                old_table_name = f"_{table_name}__old"
                statements.append(
                    f"ALTER TABLE {table_name} RENAME TO {old_table_name};"
                )
                statements.append(
                    self._format_create_table(
                        table_name,
                        (
                            *changes["alter"],
                            *changes["create"],
                            *changes["no_change"],
                        ),
                    )
                )
                statements.append(
                    self._transfer_data(
                        old_table_name,
                        table_name,
                        (*changes["alter"], *changes["no_change"]),
                    )
                )
                statements.append(f"DROP TABLE {old_table_name};")

        return statements

    def _build_create_statements(self, diff):
        statements = []

        for table_name, rows in diff.items():
            statements.append(self._format_create_table(table_name, rows))

        return statements

    def _format_create_table(self, table_name, rows):
        statement = f"CREATE TABLE {table_name} ("
        for i, row in enumerate(rows):
            statement += self._format_column(row, add_comma=(i + 1 != len(rows)))

        statement += ");"
        return statement

    def _format_column(self, row, add_comma=True):
        return (
            f"{row['name']} {row['type']}{' NOT NULL' if row['notnull'] else ''}"
            f"{f' DEFAULT {row[DEFAULT_VALUE]}' if row[DEFAULT_VALUE] is not None else ''}"
            f"{' PRIMARY KEY' if row['is_pk'] else ''}{',' if add_comma else ''}"
        )

    def _transfer_data(self, old_table_name, table_name, rows):
        col_names = [row["name"] for row in rows]
        col_names = ", ".join(col_names)
        statement = (
            f"INSERT INTO {table_name} ({col_names}) "
            f"SELECT {col_names} FROM {old_table_name};"
        )
        return statement


class DatabaseSchemaReader(BaseDatabaseSchemaReader):
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
                    "name": row[1],
                    "type": row[2],
                    "notnull": bool(row[3]),
                    "default_value": row[4],
                    "is_pk": bool(row[5]),
                }
            )

        return formatted_rows
