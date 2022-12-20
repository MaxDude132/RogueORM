from unittest import TestCase, skip

from rogue.models import Model, Field
from rogue.backends.sqlite.client import DatabaseClient


class TestModel(Model):
    test: Field[int]


class ModelTestCase(TestCase):
    def setUp(self):
        self.client = DatabaseClient("default.sqlite")
        self.client.execute(
            "CREATE TABLE test_model (id integer PRIMARY KEY autoincrement, test integer);"
        )

    def test_wrong_model_definitions(self):
        # Field needs to be passed a Python type
        with self.assertRaises(TypeError):

            class WrongTestModel(Model):
                test: Field

        # Field cannot have more than one Python type
        with self.assertRaises(AssertionError):

            class WrongTestModel(Model):
                test: Field[str, int]

        # Field cannot have more than one Python type, part 2
        with self.assertRaises(AssertionError):

            class WrongTestModel(Model):
                test: Field[str | int]

        # Raises error if the Python type has not yet been handled
        # (should be possible to remove most if not all of these in the future)
        with self.assertRaises(TypeError):

            class WrongTestModel(Model):
                test: Field[dict]

    def test_model_definitions(self):
        class DefinedModel(Model):
            string_field: Field[str](max_char=10)
            field_with_tuple_len_1: Field[
                str,
            ](max_char=10)
            nullable_field: Field[int | None]

        self.assertEqual(DefinedModel.string_field.max_char, 10)
        self.assertEqual(DefinedModel.field_with_tuple_len_1.max_char, 10)

        self.assertFalse(DefinedModel.string_field.nullable)
        self.assertFalse(DefinedModel.field_with_tuple_len_1.nullable)
        self.assertTrue(DefinedModel.nullable_field.nullable)

    def test_save_model(self):
        test_model = TestModel(test=3)
        test_model.save()

        self.assertIsNotNone(test_model.id)

    def test_get_model(self):
        self.client.execute("INSERT INTO test_model (test) VALUES (42)")
        row = TestModel.get(id=1)
        self.assertEqual(row.test, 42)

    def test_get_all_models(self):
        self.client.execute("INSERT INTO test_model (test) VALUES (42), (49), (56)")
        rows = TestModel.all()

        for row, expected_value in zip(rows, (42, 49, 56)):
            self.assertEqual(row.test, expected_value)

    def tearDown(self) -> None:
        self.client.execute("DROP TABLE test_model;")
