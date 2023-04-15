import os
from unittest import TestCase

from rogue.migrations import makemigrations, migrate


class MigrationTestCase(TestCase):
    def test_makemigrations(self):
        makemigrations()
