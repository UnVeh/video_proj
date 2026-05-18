import pytest
from defect_ai_mock import DefectAIMock


def test_no_detection():
    """
    Если вероятность = 0, дефекты никогда не должны появляться
    """
    ai = DefectAIMock(detection_probability=0.0)
    result = ai.analyze_frame(None, 100)
    assert result is None


def test_always_detect():
    """
    Если вероятность = 1, дефект должен быть всегда
    """
    ai = DefectAIMock(detection_probability=1.0)
    result = ai.analyze_frame(None, 100)
    assert result in range(1, 8)


def test_sequence_grouping():
    """
    Проверяем, что последовательность кадров возвращает список сегментов
    """
    ai = DefectAIMock(detection_probability=1.0)

    frames = [(None, i * 10) for i in range(5)]
    result = ai.analyze_sequence(frames)

    assert isinstance(result, list)
    assert all(len(r) == 3 for r in result)


def test_defect_name():
    """
    Проверка маппинга код → название
    """
    assert DefectAIMock.get_defect_name(1) == "выбоина"
    assert DefectAIMock.get_defect_name(999) == "неизвестно"


def test_invalid_probability():
    ai = DefectAIMock(detection_probability=-1)
    assert ai.detection_probability == -1