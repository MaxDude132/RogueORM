import os
from unittest import TestCase
from sqlite3 import Connection as SqliteConnection, Cursor as SqliteCursor

from rogue.backends.sqlite.client import DatabaseClient


class DatabaseClientTestCase(TestCase):
    def setUp(self):
        self.database_client = DatabaseClient("test_database.sqlite")

    def test_connection(self):
        connection = self.database_client.get_connection()
        self.assertIsInstance(connection, SqliteConnection)

    def test_execute(self):
        statement = "CREATE TABLE test_client (test_column integer PRIMARY KEY);"
        response = self.database_client.execute(statement)
        self.assertIsInstance(response, SqliteCursor)

        value = 25
        statement = "INSERT INTO test_client (test_column) VALUES(?)"
        response = self.database_client.execute(statement, (value,))
        self.assertIsInstance(response, SqliteCursor)

        statement = "SELECT * FROM test_client;"
        response = self.database_client.execute(statement)
        self.assertIsInstance(response, SqliteCursor)

    def tearDown(self) -> None:
        self.database_client.close()
        os.remove("test_database.sqlite")
