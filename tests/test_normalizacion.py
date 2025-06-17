import pytest
from core import normaliza_banda, agrupar_tech

@pytest.mark.parametrize("input_b, input_t, expected", [
    ("B7", "", "2600"),
    ("7",  "", "2600"),
    ("NR2100", "", "2100"),
    ("3500", "", "78"),
    ("N78", "", "78"),
    ("foo",   "", "FOO"),      # fallback
])
def test_normaliza_banda(input_b, input_t, expected):
    assert normaliza_banda(input_b, input_t) == expected

@pytest.mark.parametrize("tech_str, expected", [
    ("5G-NR", "5G"),
    ("NR",    "5G"),
    ("4G",    "4G"),
    ("LTE",   "4G"),
    ("NBIOT", "NBIOT"),
    ("xyz",   "XYZ"),           # uppercase fallback
])
def test_agrupar_tech(tech_str, expected):
    assert agrupar_tech(tech_str) == expected
