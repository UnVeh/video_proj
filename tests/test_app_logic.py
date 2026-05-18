import pytest
from unittest.mock import MagicMock
from app import App


@pytest.fixture
def app():
    root = MagicMock()
    root.after = lambda t, f: f()

    app = App(root, build_ui=False)

    # ======================
    # MOCK UI DEPENDENCIES
    # ======================
    app.forward_frame = MagicMock()
    app.reverse_frame = MagicMock()

    app.update_forward_column = MagicMock()
    app.update_reverse_column = MagicMock()
    app.update_buttons_state = MagicMock()

    app.error_var.set = MagicMock()

    return app


# =========================
# KM utils
# =========================

def test_km_to_meters(app):
    assert app.km_to_meters("1+000") == 1000
    assert app.km_to_meters("12+345") == 12345
    assert app.km_to_meters("bad") == 0


def test_meters_to_km(app):
    assert app.meters_to_km(1000) == "1+000"


# =========================
# apply_result
# =========================

def test_apply_result_success(app):
    path = "video.avi"

    app.apply_result(path, "1+000", "2+000", False, "forward")

    assert app.analysis_status[path] is False
    assert app.analysis_error[path] is False
    assert app.saved_settings[path]["start"] == "1+000"
    assert app.video_bounds[path]["start"] == 1000


def test_apply_result_error(app):
    path = "video.avi"

    app.apply_result(path, "", "", True, "forward")

    assert app.analysis_error[path] is True
    assert app.saved_settings[path]["start"] == ""


# =========================
# remove file
# =========================

def test_remove_forward_file(app):
    file = "test.avi"

    app.road_files.append(file)
    app.saved_settings[file] = {"start": "1+000", "end": "2+000"}
    app.analysis_status[file] = True

    app.remove_forward_file(file)

    assert file not in app.road_files
    assert file not in app.saved_settings


def test_remove_nonexistent_file(app):
    app.remove_forward_file("ghost.avi")  # не падает


# =========================
# change_km
# =========================

def test_change_km_out_of_bounds(app):
    var = MagicMock()
    other = MagicMock()

    var.get.return_value = "1+000"
    other.get.return_value = "2+000"

    app.change_km(var, other, 100000, 0, 2000, True)

    app.error_var.set.assert_called()