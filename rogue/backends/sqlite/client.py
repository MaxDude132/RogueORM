from backends.base import BaseDatabaseClient
import sqlite3


class DatabaseClient(BaseDatabaseClient):
    def get_connection(self):
        if self._connection is None:
            self._connection = sqlite3.connect(self._db_name)

        return self._connection

    def execute(self, statement, *args):
        connection = self.get_connection()
        data = connection.execute(statement, args)
        connection.commit()

        return data

    def close(self):
        self.get_connection().close()
