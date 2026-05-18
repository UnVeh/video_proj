import pytest
from detect2 import KmExtractor


@pytest.fixture
def extractor():
    return KmExtractor("dummy.mp4")


def test_extract_kilometer_basic(extractor):
    assert extractor.extract_kilometer("12 км") == "12"
    assert extractor.extract_kilometer("12.5 км") == "12.5"
    assert extractor.extract_kilometer("12,5 км") == "12.5"


def test_extract_kilometer_empty_and_invalid(extractor):
    assert extractor.extract_kilometer("") is None
    assert extractor.extract_kilometer(None) is None
    assert extractor.extract_kilometer("abcdef") is None
    assert extractor.extract_kilometer("!!!@@@###") is None
    assert extractor.extract_kilometer("км") is None



def test_extract_kilometer_glued(extractor):
    assert extractor.extract_kilometer("12км") == "12"
    assert extractor.extract_kilometer("12.34км") == "12.34"
    assert extractor.extract_kilometer("0км") == "0"



def test_extract_kilometer_with_noise(extractor):
    assert extractor.extract_kilometer("  12 км  ") == "12"
    assert extractor.extract_kilometer("\n12 км\n") == "12"
    assert extractor.extract_kilometer("km 12 км") == "12"


def test_extract_kilometer_locale_variants(extractor):
    assert extractor.extract_kilometer("12,5 км") == "12.5"
    assert extractor.extract_kilometer("1,0 км") == "1.0"
    assert extractor.extract_kilometer("0,75км") == "0.75"


def test_extract_kilometer_edge_cases(extractor):
    assert extractor.extract_kilometer("0 км") == "0"
    assert extractor.extract_kilometer("0.0 км") == "0.0"
    assert extractor.extract_kilometer("999999 км") == "999999"


def test_extract_kilometer_weird_ocr(extractor):
    assert extractor.extract_kilometer("12 к м") == "12"
    assert extractor.extract_kilometer("12км.") == "12"
    
def test_extract_kilometer_none_input(extractor):
    assert extractor.extract_kilometer(None) is None
    
def test_extract_kilometer_separators(extractor):
    assert extractor.extract_kilometer("12-км") == "12"
    assert extractor.extract_kilometer("12/км") == "12"
    assert extractor.extract_kilometer("12|км") == "12"
    
def test_extract_kilometer_broken_number(extractor):
    assert extractor.extract_kilometer("1 2 км") is None
    
def test_extract_kilometer_false_positive(extractor):
    assert extractor.extract_kilometer("нет данных 12км/ч скорость") == "12"
    
def test_extract_kilometer_bad_decimal(extractor):
    assert extractor.extract_kilometer("12..5 км") is None
    assert extractor.extract_kilometer("12,,5 км") is None
    
def test_extract_kilometer_real_ocr_noise(extractor):
    assert extractor.extract_kilometer(">>> 12 , 5 км <<<") == "12.5"
    
def test_extract_kilometer_only_unit(extractor):
    assert extractor.extract_kilometer("км км км") is None