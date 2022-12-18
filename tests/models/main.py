from unittest import TestCase

from rogue.models import Model


class TestModel(Model):
    pass


class ModelTestCase(TestCase):
    def test_create_model(self):
        test_model = TestModel()
