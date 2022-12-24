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
        self.client.execute(
            "CREATE TABLE error_defined_model (id integer PRIMARY KEY autoincrement, "
            "test_model_id integer NOT NULL, other_test_model_id integer, "
            "FOREIGN KEY(test_model_id) REFERENCES test_model (id), "
            "FOREIGN KEY(other_test_model_id) REFERENCES test_model (id));"
        )
        self.client.execute(
            "CREATE TABLE m2m_defined_model (id integer PRIMARY KEY autoincrement);"
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
                reverse_name="other_reverse_name"  # noqa: F821
            )

        # test_model not passed, but it is not nullable
        with self.assertRaises(FieldValidationError):
            defined_model = DefinedModel(test=5)

        test_model = TestModel(test=5)
        test_model.save()
        defined_model = DefinedModel(test_model=test_model)
        defined_model.save()

        other_defined_model = DefinedModel(test_model=test_model)
        other_defined_model.save()

        wrong_test_model = TestModel(test=6)
        wrong_defined_model = DefinedModel(test_model=wrong_test_model)
        wrong_defined_model.save()

        self.assertEqual(defined_model.test_model.id, test_model.id)
        self.assertIsNone(defined_model.other_test_model)

        self.assertIn(defined_model, test_model.defined_model_set)
        self.assertIn(other_defined_model, test_model.defined_model_set)
        self.assertNotIn(wrong_defined_model, test_model.defined_model_set)
        self.assertNotIn(wrong_test_model, test_model.defined_model_set)

        # Make sure the cache is used and the DB is not hit each time
        self.assertIs(defined_model.test_model, defined_model.test_model)

    def test_model_with_one_to_one_relationship(self):
        # 2 related fields with the same name
        with self.assertRaises(FieldValidationError):

            class ErrorDefinedModel(Model):
                test_model: Field[TestModel](one_to_one=True)
                other_test_model: Field[TestModel | None](one_to_one=True)

        class DefinedModel(Model):
            test_model: Field[TestModel](one_to_one=True)
            other_test_model: Field[TestModel | None](
                reverse_name="reverse_name", one_to_one=True  # noqa: F821
            )

        # test_model not passed, but it is not nullable
        with self.assertRaises(FieldValidationError):
            defined_model = DefinedModel(test=5)

        test_model = TestModel(test=5)
        defined_model = DefinedModel(test_model=test_model)
        defined_model.save()

        self.assertIsNotNone(defined_model.test_model)
        self.assertIsNotNone(test_model.defined_model)
        self.assertIsNone(defined_model.other_test_model)

        self.assertEqual(test_model.id, defined_model.test_model.id)
        self.assertEqual(defined_model.id, test_model.defined_model.id)

    def test_model_with_many_to_many_relationship(self):
        # 2 related fields with the same name
        with self.assertRaises(FieldValidationError):

            class ErrorM2MDefinedModel(Model):
                test_models: Field[TestModel](many_to_many=True)
                other_test_models: Field[TestModel | None](many_to_many=True)

        class M2mDefinedModel(Model):
            test_models: Field[TestModel](many_to_many=True)
            other_test_models: Field[TestModel | None](
                reverse_name="many_reverse_name", many_to_many=True  # noqa: F821
            )

        test_model = TestModel(test=5)
        test_model.save()
        defined_model = M2mDefinedModel(test_models=[test_model])
        defined_model.save()

        defined_model = M2mDefinedModel.get(id=defined_model.id)

        print(defined_model)
        print(defined_model.test_models)

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

    def test_delete_model(self):
        self.client.execute("INSERT INTO test_model (test) VALUES (42)")
        model = TestModel.get(test=42)
        model.delete()
        self.assertIsNone(model.id)

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
        self.client.execute("DROP TABLE error_defined_model;")
        self.client.execute("DROP TABLE m2m_defined_model;")
