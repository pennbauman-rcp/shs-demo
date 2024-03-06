import pytest
import math
from parse import *

# Helper function to compare floats
def approx_eq_floats(a: float, b: float) -> bool:
    return math.isclose(a, b, rel_tol=0.00001)


def test_dms2float_degrees():
    assert approx_eq_floats(dms2float("N10*"), 10)

def test_dms2float_degrees_minutes():
    assert approx_eq_floats(dms2float("N10*25'"), 10.4167)

def test_dms2float_degrees_minutes_seconds():
    assert approx_eq_floats(dms2float("N10*25'50\""), 10.4305)

def test_dms2float_unicode():
    assert approx_eq_floats(dms2float("N10°25′50″"), 10.4305)

def test_dms2float_spaced():
    assert approx_eq_floats(dms2float("\tN10*25'50\"   "), 10.4305)
    assert approx_eq_floats(dms2float("N10* 25' 50\" "), 10.4305)

def test_dms2float_trailing_direction():
    assert approx_eq_floats(dms2float("32° 54' 52.92\" N"), 32.9147)
    assert approx_eq_floats(dms2float("7° 25' 27.77\" S"), -7.4244)

def test_dms2float_implicit_units():
    assert approx_eq_floats(dms2float("N10"), 10)
    assert approx_eq_floats(dms2float("N10*25"), 10.4167)
    assert approx_eq_floats(dms2float("N10*25'50"), 10.4305)

def test_dms2float_decimals():
    # Trailing
    assert approx_eq_floats(dms2float("N10.9*"), 10.9)
    assert approx_eq_floats(dms2float("N10*25.9'"), 10.4317)
    assert approx_eq_floats(dms2float("N10*25'50.9\""), 10.4308)
    # Mid string
    assert approx_eq_floats(dms2float("N10.9*25'50\""), 11.3305)
    assert approx_eq_floats(dms2float("N10*25.9'50\""), 10.4456)


def test_dms2float_implicit_directions():
    assert approx_eq_floats(dms2float("10*"), 10)
    assert approx_eq_floats(dms2float("-10*"), -10)

def test_dms2float_all_directions():
    assert approx_eq_floats(dms2float("N10*"),  10)
    assert approx_eq_floats(dms2float("S10*"), -10)
    assert approx_eq_floats(dms2float("E10*"),  10)
    assert approx_eq_floats(dms2float("W10*"), -10)
    assert approx_eq_floats(dms2float("n10*"),  10)
    assert approx_eq_floats(dms2float("s10*"), -10)
    assert approx_eq_floats(dms2float("e10*"),  10)
    assert approx_eq_floats(dms2float("w10*"), -10)

def test_dms2float_invalid_direction():
    with pytest.raises(Exception):
        dms2float("X10*25'50\"")

def test_dms2float_invalid_unit_order():
    with pytest.raises(Exception):
        dms2float("N10*25\"50'")


def test_parse_coord_ne():
    a, b = parse_coord("N35°10.25' / E79°0.87'")
    assert approx_eq_floats(a, 35.1708)
    assert approx_eq_floats(b, 79.0145)

def test_parse_coord_sw():
    a, b = parse_coord("S38°15.87' / W121°55.45'")
    assert approx_eq_floats(a, -38.2645)
    assert approx_eq_floats(b, -121.9242)

def test_parse_coord_comma():
    a, b = parse_coord("N26°21'34\",E127°46'06\"")
    assert approx_eq_floats(a, 26.3594)
    assert approx_eq_floats(b, 127.7683)
