from unittest import TestCase

from rogue.models import Model, Field
from rogue.backends.sqlite.client import DatabaseClient


class TestModel(Model):
    test: Field[int]


class ModelTestCase(TestCase):
    def setUp(self):
        self.client = DatabaseClient("DB_NAME_TO_BE_SET.sqlite")
        self.client.execute(
            "CREATE TABLE test_model (id integer PRIMARY KEY, test integer);"
        )

    def test_create_model(self):
        test_model = TestModel()
        print(test_model)

    def tearDown(self) -> None:
        self.client.execute("DROP TABLE test_model;")
