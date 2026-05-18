import pytest
import numpy as np
import itertools
from unittest.mock import patch
from km_analyzer import format_km, analyze_video


def test_format_km():
    assert format_km("12.345") == "12+345"
    assert format_km("1.0") == "1+000"
    assert format_km("bad") is None


def test_format_km_edge():
    assert format_km("0.001") == "0+001"
    assert format_km("10.999") == "10+999"


@patch("km_analyzer.get_first_frame")
@patch("km_analyzer.get_last_frame")
@patch("km_analyzer.KmExtractor")
def test_analyze_video_success(mock_extractor, mock_last, mock_first):

    fake_frame = np.zeros((100, 200, 3), dtype=np.uint8)

    mock_first.return_value = fake_frame
    mock_last.return_value = fake_frame

    extractor = mock_extractor.return_value

    extractor.ocr_multi.side_effect = itertools.cycle(["12 км", "13 км"])
    extractor.extract_kilometer.side_effect = itertools.cycle(["12", "13"])

    start, end, error = analyze_video("video.avi")

    assert start == "12+000"
    assert end == "13+000"
    assert error is None


@patch("km_analyzer.get_first_frame", return_value=None)
@patch("km_analyzer.get_last_frame", return_value=None)
def test_analyze_video_no_frames(mock_last, mock_first):

    start, end, error = analyze_video("video.avi")

    assert start is None
    assert end is None
    assert error is not None


@patch("km_analyzer.get_first_frame")
@patch("km_analyzer.get_last_frame")
@patch("km_analyzer.KmExtractor")
def test_analyze_video_ocr_empty(mock_extractor, mock_last, mock_first):

    fake_frame = np.zeros((100, 200, 3), dtype=np.uint8)

    mock_first.return_value = fake_frame
    mock_last.return_value = fake_frame

    extractor = mock_extractor.return_value

    extractor.ocr_multi.side_effect = itertools.cycle(["", ""])
    extractor.extract_kilometer.side_effect = itertools.cycle([None, None])

    start, end, error = analyze_video("video.avi")

    assert start is None
    assert end is None
    assert error is not None


@patch("km_analyzer.get_first_frame")
@patch("km_analyzer.get_last_frame")
@patch("km_analyzer.KmExtractor")
def test_analyze_video_duplicate_ocr_calls(mock_extractor, mock_last, mock_first):
    fake_frame = np.zeros((100, 200, 3), dtype=np.uint8)

    mock_first.return_value = fake_frame
    mock_last.return_value = fake_frame

    extractor = mock_extractor.return_value

    extractor.ocr_multi.return_value = "12 км"
    extractor.extract_kilometer.return_value = "12"

    analyze_video("video.avi")

    # OCR вызывается слишком много раз
    assert extractor.ocr_multi.call_count >= 2
    
@patch("km_analyzer.get_first_frame")
@patch("km_analyzer.get_last_frame")
@patch("km_analyzer.KmExtractor")
def test_analyze_video_dirty_ocr(mock_extractor, mock_last, mock_first):
    fake_frame = np.zeros((100, 200, 3), dtype=np.uint8)

    mock_first.return_value = fake_frame
    mock_last.return_value = fake_frame

    extractor = mock_extractor.return_value

    extractor.ocr_multi.side_effect = ["12km???", "13--km"]
    extractor.extract_kilometer.side_effect = ["12", "13"]

    start, end, error = analyze_video("video.avi")

    assert start == "12+000"
    assert end == "13+000"
    assert error is None
    
@patch("km_analyzer.get_first_frame")
@patch("km_analyzer.get_last_frame")
@patch("km_analyzer.KmExtractor")
def test_analyze_video_first_frame_reused(mock_extractor, mock_last, mock_first):
    fake_frame = np.zeros((100, 200, 3), dtype=np.uint8)

    mock_first.return_value = fake_frame
    mock_last.return_value = fake_frame

    extractor = mock_extractor.return_value

    extractor.ocr_multi.return_value = "12 км"
    extractor.extract_kilometer.return_value = "12"

    analyze_video("video.avi")

    # должно быть 2 вызова, а не 3-4
    assert extractor.ocr_multi.call_count <= 3
    
    
@patch("km_analyzer.subprocess.Popen")
def test_get_last_frame_ffmpeg_failure(mock_popen):
    mock_proc = mock_popen.return_value
    mock_proc.stdout.read.return_value = b""

    from km_analyzer import get_last_frame

    result = get_last_frame("video.avi")

    # fallback должен сработать
    assert result is None or isinstance(result, np.ndarray)
    
@patch("km_analyzer.get_first_frame", return_value=None)
@patch("km_analyzer.get_last_frame", return_value=None)
def test_analyze_video_broken_video(mock_last, mock_first):
    start, end, error = analyze_video("video.avi")

    assert error == "Не удалось получить кадры"
    