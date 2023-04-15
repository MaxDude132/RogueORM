from unittest import TestCase

from rogue.models import Model, Field
from rogue.backends.sqlite.client import DatabaseClient
from rogue.managers.errors import ManagerValidationError
from rogue.settings import settings


class TestManager(Model):
    test: Field[int | None]


class TestModel(Model):
    test_manager: Field[TestManager]


class ManagerTestCase(TestCase):
    def setUp(self):
        self.client = DatabaseClient(settings.DATABASE_NAME)
        self.client.execute(
            "CREATE TABLE test_manager (id integer PRIMARY KEY autoincrement, test integer);"
        )
        self.client.execute(
            "CREATE TABLE test_model (id integer PRIMARY KEY autoincrement, test_manager_id integer);"
        )
        self.test_model = TestManager()
        self.manager = self.test_model._get_new_manager()

    def test_wrong_insert(self):
        # Without data
        with self.assertRaises(ManagerValidationError):
            self.manager.insert(None)

        # Wrong fields
        with self.assertRaises(ManagerValidationError):
            self.manager.insert({"wrong_field": 5})

    def test_insert(self):
        new_model = self.manager.insert({"test": 5})
        self.assertEqual(new_model["test"], 5)

    def test_update(self):
        self.client.execute("INSERT INTO test_manager (test) VALUES (0);")
        id_ = self.client.execute(
            "SELECT id FROM test_manager WHERE test = 0;"
        ).fetchone()[0]
        new_model = self.manager.update(id_, {"test": 5})
        self.assertEqual(new_model["test"], 5)

    def test_repr_works(self):
        str(self.manager)

    def test_equality(self):
        self.client.execute("INSERT INTO test_manager (test) VALUES (2), (4), (25);")
        other_manager = self.test_model._get_new_manager()
        self.assertEqual(self.manager, other_manager)

        other_manager.where(test__in=(2, 4))
        self.assertNotEqual(self.manager, other_manager)

    def test_comparison_operators(self):
        self.client.execute("INSERT INTO test_manager (test) VALUES (1), (2), (3);")
        self.client.execute(
            "INSERT INTO test_model (test_manager_id) VALUES (1), (2), (3);"
        )

        with self.assertRaises(LookupError):
            TestManager.where(test__wrong_operator=2)

        manager = TestManager.where(test=2)
        self.assertEqual(manager.first().test, 2)

        test_values = (1, 3)
        manager = TestManager.where(test__in=test_values)
        for model in manager:
            self.assertIn(model.id, test_values)

        manager = TestManager.where_not(test=2)
        for model in manager:
            self.assertIn(model.id, test_values)

        manager = TestManager.where_not(test__in=test_values)
        self.assertEqual(manager.first().test, 2)

        manager = TestModel.where(test_manager__test=2)
        for model in manager:
            self.assertEqual(model.test_manager.test, 2)

    def test_none(self):
        self.assertFalse(TestManager.none())

    def tearDown(self) -> None:
        self.client.execute("DROP TABLE test_manager;")
        self.client.execute("DROP TABLE test_model;")
