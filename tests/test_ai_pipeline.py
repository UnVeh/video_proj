import pytest
from unittest.mock import patch, MagicMock
from km_analyzer import run_ai_analysis


@patch("km_analyzer.cv2.VideoCapture")
@patch("km_analyzer.DefectAIMock")
def test_run_ai_analysis_basic(mock_ai, mock_cap):
    cap = MagicMock()
    cap.read.side_effect = [
        (True, "frame1"),
        (True, "frame2"),
        (False, None)
    ]
    cap.get.return_value = 2
    mock_cap.return_value = cap

    ai = mock_ai.return_value
    ai.analyze_frame.side_effect = [1, None]

    result = run_ai_analysis("video.mp4", "0+000", "0+200")

    assert isinstance(result, list)


@patch("km_analyzer.cv2.VideoCapture")
@patch("km_analyzer.DefectAIMock")
def test_run_ai_analysis_empty_video(mock_ai, mock_cap):
    cap = MagicMock()
    cap.read.return_value = (False, None)
    cap.get.return_value = 0
    mock_cap.return_value = cap

    ai = mock_ai.return_value
    ai.analyze_frame.return_value = None

    result = run_ai_analysis("video.mp4", "0+000", "0+200")

    assert isinstance(result, list)


def test_invalid_km_range():
    result = run_ai_analysis("video.mp4", "1+000", "0+500")
    assert result == []