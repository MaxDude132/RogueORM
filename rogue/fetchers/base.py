from rogue.backends.sqlite.client import DatabaseClient
from rogue.backends.sqlite.query import QueryBuilder


class Fetcher:
    def get_client(self, db_name):
        if not hasattr(self, "_client"):
            self._client = DatabaseClient(db_name)

        return self._client

    def get_values(self, table, pks):
        data = (
            QueryBuilder(self.get_client("DB_NAME_TO_BE_SET.sqlite"))
            .select_from(table)
            .where("id", "IN", pks)
            .get_all()
        )
        return data
