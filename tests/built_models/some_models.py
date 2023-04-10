from rogue.models.base import Model
from rogue.models.fields import Field


class SomeModelForTesting(Model):
    first_field: Field[str](max_char=40)
    second_field: Field[str | None](max_char=20)


class SomeOtherModelForTesting(Model):
    first_field: Field[str](max_char=20)
    second_field: Field[str | None](max_char=20)


class SomeOtherOtherModelForTesting(Model):
    first_field: Field[str](max_char=20)
    second_field: Field[str | None](max_char=20)
