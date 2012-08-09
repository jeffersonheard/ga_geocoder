"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from django.test import TestCase
from django.contrib.gis.geos import Point
from unittest import skip

from ga_geocoder import utils
from ga_geocoder.parsers import independent, en_us

test_file = '/Users/jeff/Source/ga_geocoder/ga_geocoder/fixtures/tl_2010_37_zcta510.shp'
test_layer = 'tl_2010_37_zcta510'
test_field = 'ZCTA5CE10'
test_codes = ["27713", "27707", "27516"]

class IndependentParserTest(TestCase):
    def test_ci_shortcode(self):
        a = independent.ci_shortcode('ASDFASDFASDFASDFASDF')
        b = independent.ci_shortcode('asdfasdfasdfasdfasdf')
        c = independent.ci_shortcode(' asdfasdfasdfasdfasdf')
        d = independent.ci_shortcode('asdfasdfasdfasdfasdf ')
        self.assertEqual(a, b)
        self.assertEqual(b, c)
        self.assertEqual(c, d)
        self.assertNotEqual(a, 'ASDFASDFASDFASDFASDF')

    def test_cs_shortcode(self):
        a = independent.cs_shortcode('ASDFASDFASDFASDFASDF')
        b = independent.cs_shortcode('asdfasdfasdfasdfasdf')
        c = independent.cs_shortcode(' asdfasdfasdfasdfasdf')
        d = independent.cs_shortcode('asdfasdfasdfasdfasdf ')
        self.assertNotEqual(a, b)
        self.assertEqual(b, c)
        self.assertEqual(c, d)
        self.assertNotEqual(a, 'ASDFASDFASDFASDFASDF')

    def test_ci_code(self):
        a = independent.ci_code('ASDFASDFASDFASDFASDF')
        b = independent.ci_code('asdfasdfasdfasdfasdf')
        c = independent.ci_code(' asdfasdfasdfasdfasdf')
        d = independent.ci_code('asdfasdfasdfasdfasdf ')
        self.assertEqual(a, b)
        self.assertEqual(b, c)
        self.assertEqual(c, d)

    def test_cs_code(self):
        a = independent.cs_code('ASDFASDFASDFASDFASDF')
        b = independent.cs_code('asdfasdfasdfasdfasdf')
        c = independent.cs_code(' asdfasdfasdfasdfasdf')
        d = independent.cs_code('asdfasdfasdfasdfasdf ')
        self.assertNotEqual(a, b)
        self.assertEqual(b, c)
        self.assertEqual(c, d)

class UsEnParserTest(TestCase):
    def test_naive_parser(self):
        a = en_us.address_trigrams_naive('123 Abc. St., 27707')
        b = en_us.address_trigrams_naive('123 Abc St 27707')
        c = en_us.address_trigrams_naive(' 123 Abc St 27707')
        d = en_us.address_trigrams_naive('123 abc St 27707 ')
        e = en_us.address_trigrams_naive('123 Abc St  27707 ')
        f = en_us.address_trigrams_naive('1234 Abc St 27707')

        self.assertEqual(a, b)
        self.assertEqual(b, c)
        self.assertEqual(c, d)
        self.assertEqual(d, e)
        self.assertNotEqual(e, f)
        self.assertListEqual(a[0:2], ['123','27707'])

    def test_word_parser(self):
        a = en_us.address_trigrams('123 Abc. St., 27707')
        b = en_us.address_trigrams('123 Abc St 27707')
        c = en_us.address_trigrams(' 123 Abc St 27707')
        d = en_us.address_trigrams('123 abc St 27707 ')
        e = en_us.address_trigrams('123 Abc St  27707 ')
        f = en_us.address_trigrams('1234 Abc St 27707')

        self.assertEqual(a, b)
        self.assertEqual(b, c)
        self.assertEqual(c, d)
        self.assertEqual(d, e)
        self.assertNotEqual(e, f)
        self.assertListEqual(a[0:2], ['123','27707'])


class ExactGeocoderTest(TestCase):
    @classmethod
    def setUpClass(cls):
        """Load geocoder in bulk"""
        print 'foo'
        cls.coder = utils.geocoder_from_ogr(test_layer, utils.EXACT, test_file, test_layer, test_field)

    def test_single_geocode(self):
        for geom in (self.coder[code] for code in test_codes):
            self.assertIsNotNone(geom)

    def test_bulk_geocode(self):
        k = list(self.coder.bulk_geocode(test_codes))
        self.assertEqual(len(k), len(test_codes))
        for c, g in k:
            self.assertIsNotNone(g)

    def test_reverse_geocode(self):
        swarthmore = Point(-78.9597, 35.93484, srid=4326)
        code = self.coder.reverse_geocode(swarthmore)
        self.assertIsNotNone(code)

    @classmethod
    def tearDownClass(cls):
        """Drop geocoder and confirm it's gone"""
        cls.coder.drop()