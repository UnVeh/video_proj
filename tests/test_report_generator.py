import os
import pytest
from report_generator import generate_excel, generate_odm_excel


def test_generate_excel_basic(tmp_path):
    data = [
        (0, 100, [{"code": 1}])
    ]

    file = tmp_path / "test.xlsx"
    result = generate_excel(data, filename=str(file))

    assert os.path.exists(result)
    assert result.endswith(".xlsx")


def test_generate_odm_excel_basic(tmp_path):
    data = [
        (0, 100, [{"type": "pothole", "position": 10}])
    ]

    file = tmp_path / "test_odm.xlsx"
    result = generate_odm_excel(data, filename=str(file))

    assert os.path.exists(result)
    assert result.endswith(".xlsx")


def test_generate_excel_empty_data(tmp_path):
    file = tmp_path / "empty.xlsx"

    result = generate_excel([], filename=str(file))

    assert os.path.exists(result)


def test_generate_odm_excel_empty_data(tmp_path):
    file = tmp_path / "empty_odm.xlsx"

    result = generate_odm_excel([], filename=str(file))

    assert os.path.exists(result)


def test_generate_excel_return_value(tmp_path):
    data = [(0, 50, [{"code": 2}])]

    file = tmp_path / "return.xlsx"
    result = generate_excel(data, filename=str(file))

    # функция должна возвращать путь к файлу
    assert isinstance(result, str)
    assert os.path.isfile(result)


def test_generate_odm_excel_return_value(tmp_path):
    data = [(0, 50, [{"type": "pothole", "position": 5}])]

    file = tmp_path / "return_odm.xlsx"
    result = generate_odm_excel(data, filename=str(file))

    assert isinstance(result, str)
    assert os.path.isfile(result)


def test_generate_excel_overwrite(tmp_path):
    data = [(0, 100, [{"code": 1}])]

    file = tmp_path / "overwrite.xlsx"

    r1 = generate_excel(data, filename=str(file))
    r2 = generate_excel(data, filename=str(file))

    assert os.path.exists(r1)
    assert os.path.exists(r2)
    assert r1 == r2