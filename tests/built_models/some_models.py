from rogue.models.base import Model
from rogue.models.fields import Field


class SomeModelForTesting(Model):
    first_field = Field[str](max_length=20)
