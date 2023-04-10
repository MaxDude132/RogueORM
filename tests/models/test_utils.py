from unittest import TestCase

from rogue.models import Model, Field
from rogue.models.utils import get_all_models


class TestModel(Model):
    test: Field[int]


class UtilsTestCase(TestCase):
    def test_get_all_models(self):
        all_models = get_all_models()
        self.assertIn(TestModel, all_models)

        class OtherTestModel(TestModel):
            pass

        # If a model inherits from TestModel, we assume
        # it to be a static model, and should thus not be returned
        # The model that inherits should be the one returned instead
        all_models = get_all_models()
        self.assertNotIn(TestModel, all_models)
        self.assertIn(OtherTestModel, all_models)
