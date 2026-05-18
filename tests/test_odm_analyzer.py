import pytest
from odm_defect_analyzer import ODMDefectAnalyzer


def test_empty_segment():
    analyzer = ODMDefectAnalyzer()
    code, score = analyzer.analyze_defects_on_segment(0, 100)

    assert code == 1
    assert score == 5.0


def test_empty_segment_zero_length():
    analyzer = ODMDefectAnalyzer()
    code, score = analyzer.analyze_defects_on_segment(0, 0)

    assert isinstance(code, int)
    assert isinstance(score, float)



def test_transverse_cracks():
    analyzer = ODMDefectAnalyzer()

    analyzer.add_defect(0, "crack_transverse")
    analyzer.add_defect(5, "crack_transverse")

    code, score = analyzer.analyze_defects_on_segment(0, 100)

    assert code in range(1, 10)
    assert 0.0 <= score <= 5.0


def test_multiple_cracks_spread():
    analyzer = ODMDefectAnalyzer()

    for i in range(10):
        analyzer.add_defect(i * 2, "crack_transverse")

    code, score = analyzer.analyze_defects_on_segment(0, 100)

    assert code in range(1, 10)
    assert score <= 5.0



def test_potholes():
    analyzer = ODMDefectAnalyzer()

    analyzer.add_defect(0, "pothole")
    analyzer.add_defect(2, "pothole")

    code, score = analyzer.analyze_defects_on_segment(0, 100)

    assert code in [24, 25, 26, 27]
    assert score <= 5.0


def test_potholes_many():
    analyzer = ODMDefectAnalyzer()

    for i in range(5):
        analyzer.add_defect(i * 10, "pothole")

    code, score = analyzer.analyze_defects_on_segment(0, 100)

    assert isinstance(code, int)
    assert isinstance(score, float)


def test_mixed_defects():
    analyzer = ODMDefectAnalyzer()

    analyzer.add_defect(0, "pothole")
    analyzer.add_defect(10, "crack_transverse")
    analyzer.add_defect(20, "pothole")

    code, score = analyzer.analyze_defects_on_segment(0, 100)

    assert isinstance(code, int)
    assert 0.0 <= score <= 5.0


def test_unknown_defect():
    analyzer = ODMDefectAnalyzer()

    analyzer.add_defect(0, "alien_damage")

    code, score = analyzer.analyze_defects_on_segment(0, 100)

    assert isinstance(code, int)
    assert isinstance(score, float)
    assert 0.0 <= score <= 5.0


def test_duplicate_defects():
    analyzer = ODMDefectAnalyzer()

    analyzer.add_defect(0, "pothole")
    analyzer.add_defect(0, "pothole")
    analyzer.add_defect(0, "pothole")

    code, score = analyzer.analyze_defects_on_segment(0, 100)

    assert code in range(24, 28)
    assert score <= 5.0


def test_defects_outside_segment():
    analyzer = ODMDefectAnalyzer()

    analyzer.add_defect(-10, "pothole")
    analyzer.add_defect(9999, "crack_transverse")

    code, score = analyzer.analyze_defects_on_segment(0, 100)

    assert isinstance(code, int)
    assert isinstance(score, float)



def test_no_crash_large_input():
    analyzer = ODMDefectAnalyzer()

    for i in range(1000):
        analyzer.add_defect(i, "pothole")

    code, score = analyzer.analyze_defects_on_segment(0, 100)

    assert isinstance(code, int)
    assert isinstance(score, float)