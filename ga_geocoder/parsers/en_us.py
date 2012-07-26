__author__ = 'jeffersonheard'

from ga_geocoder.parsers.independent import *

address_trigrams_naive = tokens(compose_rhs(
    strip_punctuation,
    lower_case,
    split_numbers,
    squeeze_spaces,
    trigrams
))

address_trigrams = tokens(compose_rhs(
    strip_punctuation,
    lower_case,
    split_numbers,
    compose_lhs(split_spaces, trigrams)
))