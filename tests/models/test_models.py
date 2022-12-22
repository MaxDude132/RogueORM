from unittest import TestCase, skip

from rogue.models import Model, Field
from rogue.models.errors import FieldValidationError
from rogue.backends.sqlite.client import DatabaseClient


class TestModel(Model):
    test: Field[int]


class ModelTestCase(TestCase):
    def setUp(self):
        self.client = DatabaseClient("default.sqlite")
        self.client.execute(
            "CREATE TABLE test_model (id integer PRIMARY KEY autoincrement, test integer);"
        )
        self.client.execute(
            "CREATE TABLE defined_model (id integer PRIMARY KEY autoincrement, "
            "test_model_id integer NOT NULL, other_test_model_id integer, "
            "FOREIGN KEY(test_model_id) REFERENCES test_model (id), "
            "FOREIGN KEY(other_test_model_id) REFERENCES test_model (id));"
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
            field_with_default: Field[int] = 20

        self.assertEqual(DefinedModel.string_field.max_char, 10)
        self.assertEqual(DefinedModel.field_with_tuple_len_1.max_char, 10)

        self.assertFalse(DefinedModel.string_field.nullable)
        self.assertFalse(DefinedModel.field_with_tuple_len_1.nullable)
        self.assertTrue(DefinedModel.nullable_field.nullable)

    def test_model_with_foreign_key(self):
        # 2 related fields with the same name
        with self.assertRaises(FieldValidationError):

            class ErrorDefinedModel(Model):
                test_model: Field[TestModel]
                other_test_model: Field[TestModel | None]

        class DefinedModel(Model):
            test_model: Field[TestModel]
            other_test_model: Field[TestModel | None](
                reverse_name="other_reverse_name"
            )  # noqa: F821

        with self.assertRaises(FieldValidationError):
            defined_model = DefinedModel(test=5)

        test_model = TestModel(test=5)
        defined_model = DefinedModel(test_model=test_model)
        defined_model.save()

        self.assertEqual(defined_model.test_model.id, test_model.id)
        self.assertIsNone(defined_model.other_test_model)

        # Make sure the cache is used and the DB is not hit each time
        self.assertIs(defined_model.test_model, defined_model.test_model)

    def test_model_instantiations(self):
        class DefinedModel(Model):
            field_with_default: Field[int] = 20

        defined_model = DefinedModel()
        self.assertEqual(defined_model.field_with_default, 20)

        class DefinedModel(Model):
            text: Field[int]

        with self.assertRaises(FieldValidationError):
            defined_model = DefinedModel()

        with self.assertRaises(FieldValidationError):
            defined_model = DefinedModel(text="should_be_int")

        # TODO once migrations are in place: test max_char functionality

    def test_save_model(self):
        # Insert
        test_model = TestModel(test=3)
        test_model.save()
        self.assertIsNotNone(test_model.id)
        self.assertEqual(test_model.test, 3)

        # Update
        initial_id = test_model.id
        test_model.test = 5
        test_model.save()
        self.assertEqual(test_model.id, initial_id)
        self.assertEqual(test_model.test, 5)

    def test_get_model(self):
        model = TestModel.get(id=1)
        self.assertIsNone(model)

        self.client.execute("INSERT INTO test_model (test) VALUES (42)")
        model = TestModel.get(id=1)
        self.assertEqual(model.test, 42)

    def test_get_specific_models(self):
        self.client.execute("INSERT INTO test_model (test) VALUES (42), (49), (56)")
        rows = TestModel.where(test__in=(42, 56))
        self.assertEqual(len(rows), 2)

        for row, expected_value in zip(rows, (42, 56)):
            self.assertEqual(row.test, expected_value)

    def test_get_all_models(self):
        self.client.execute("INSERT INTO test_model (test) VALUES (42), (49), (56)")
        rows = TestModel.all()

        for row, expected_value in zip(rows, (42, 49, 56)):
            self.assertEqual(row.test, expected_value)

    def test_repr_works(self):
        model = TestModel(test=5)
        str(model)

    def tearDown(self) -> None:
        self.client.execute("DROP TABLE test_model;")
        self.client.execute("DROP TABLE defined_model;")
