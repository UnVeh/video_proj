import pytest
from odm_defect_analyzer import analyze_segments_with_defects


def test_segments_processing_basic():
    segments = [
        (0, 100, [{"type": "pothole", "position": 10}]),
        (100, 200, [])
    ]

    result = analyze_segments_with_defects(segments)

    assert len(result) > 0
    assert all(len(r) == 3 for r in result)


def test_empty_segments():
    result = analyze_segments_with_defects([])
    assert result == []


def test_single_segment_no_defects():
    segments = [
        (0, 100, [])
    ]

    result = analyze_segments_with_defects(segments)

    assert len(result) == 1
    start, end, (code, score) = result[0]

    assert start == 0
    assert end == 100
    assert code == 1
    assert score == 5.0


def test_unknown_defect_does_not_crash():
    segments = [
        (0, 100, [{"type": "unknown_type", "position": 50}])
    ]

    result = analyze_segments_with_defects(segments)

    assert len(result) == 1
    assert result[0][2][0] in range(1, 30)


def test_multiple_defects_same_segment():
    segments = [
        (0, 100, [
            {"type": "pothole", "position": 10},
            {"type": "pothole", "position": 20},
            {"type": "pothole", "position": 30},
        ])
    ]

    result = analyze_segments_with_defects(segments)

    assert len(result) == 1
    code, score = result[0][2]

    assert isinstance(code, int)
    assert isinstance(score, float)


def test_segment_chopping_logic():
    segments = [
        (0, 250, [{"type": "pothole", "position": 10}])
    ]

    result = analyze_segments_with_defects(segments, segment_length=100)

    # должно разбить на 3 сегмента: 0-100, 100-200, 200-250
    assert len(result) == 3

    assert result[0][0] == 0
    assert result[1][0] == 100
    assert result[2][0] == 200


def test_defect_position_defaulting():
    # position отсутствует → должно не падать
    segments = [
        (0, 100, [{"type": "pothole"}])
    ]

    result = analyze_segments_with_defects(segments)

    assert len(result) == 1
    assert result[0][2][0] in range(1, 30)