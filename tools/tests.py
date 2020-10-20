from unittest import TestCase

from validators import validate_age
from validators import gender_hru


class ValidatorsTestCase(TestCase):

    def test_validate_age_not_int(self):
        r = validate_age('heh')
        self.assertIsNone(r)

    def test_validate_age(self):
        r = validate_age('18')
        self.assertEqual(r, 18)

    def test_validate_age_invalid_interval(self):
        r = validate_age('-1')
        self.assertIsNone(r)

        r = validate_age('112')
        self.assertIsNone(r)

    def test_gender_hru(self):
        r = gender_hru(2)
        self.assertEqual(r, 'женский')
