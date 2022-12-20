from unittest import TestCase

from rogue.models import Model, Field
from rogue.backends.sqlite.client import DatabaseClient
from rogue.backends.errors import OperationalError


class TestModel(Model):
    test: Field[int | None]


class ManagerTestCase(TestCase):
    def setUp(self):
        self.client = DatabaseClient("default.sqlite")
        self.client.execute(
            "CREATE TABLE test_manager (id integer PRIMARY KEY autoincrement, test integer);"
        )
        self.test_model = TestModel()
        self.manager = self.test_model._get_new_manager()

    def test_wrong_insert(self):
        # Without data
        with self.assertRaises(OperationalError):
            self.manager.insert(None)

    def tearDown(self) -> None:
        self.client.execute("DROP TABLE test_manager;")
