import os
from unittest.mock import patch
from streamlit.testing.v1 import AppTest


def _make_patches(tmp_path):
    """Return a list of active patch context managers for data isolation."""
    data_dir = str(tmp_path / "data")
    users_dir = os.path.join(data_dir, "users")
    return (
        patch("modules.data_manager.DATA_DIR", data_dir),
        patch("modules.data_manager.USERS_DIR", users_dir),
    )


def _run_app(tmp_path):
    """Create and run AppTest with data_dirs patched."""
    p1, p2 = _make_patches(tmp_path)
    with p1, p2:
        at = AppTest.from_file("src/app.py", default_timeout=30)
        at.run()
    return at


def _navigate_to(tmp_path, page_label):
    """Run app, select a sidebar radio option, and re-run."""
    p1, p2 = _make_patches(tmp_path)
    with p1, p2:
        at = AppTest.from_file("src/app.py", default_timeout=30)
        at.run()
        at.sidebar.radio[0].set_value(page_label).run()
    return at


# =====================================================================
# Smoke tests
# =====================================================================

def test_app_renders_without_error(tmp_path):
    at = _run_app(tmp_path)
    assert not at.exception


def test_sidebar_has_athlete_selector(tmp_path):
    at = _run_app(tmp_path)
    selectboxes = at.sidebar.selectbox
    assert len(selectboxes) >= 1
    # Default user should be in the options
    assert "default" in selectboxes[0].options


def test_sidebar_has_navigation(tmp_path):
    at = _run_app(tmp_path)
    radios = at.sidebar.radio
    assert len(radios) >= 1
    options = radios[0].options
    assert "Command Center" in options
    assert "Journal" in options
    assert "Settings" in options


def test_settings_page_has_model_selector(tmp_path):
    at = _navigate_to(tmp_path, "Settings")
    assert not at.exception
    # Find model selectbox in main area
    selectboxes = at.selectbox
    model_opts = None
    for sb in selectboxes:
        if "deepseek-r1:8b" in sb.options:
            model_opts = sb.options
            break
    assert model_opts is not None


def test_settings_page_has_prompt_editor(tmp_path):
    at = _navigate_to(tmp_path, "Settings")
    assert not at.exception
    text_areas = at.text_area
    found = any(ta.key == "system_prompt_editor" for ta in text_areas)
    assert found


def test_settings_page_has_garmin_section(tmp_path):
    at = _navigate_to(tmp_path, "Settings")
    assert not at.exception
    subheaders = [sh.value for sh in at.subheader]
    assert any("Garmin" in s for s in subheaders)


def test_journal_page_has_form(tmp_path):
    at = _navigate_to(tmp_path, "Journal")
    assert not at.exception
    # Should have sliders (RPE, Soreness) and text_area (Notes)
    assert len(at.slider) >= 1
    assert len(at.text_area) >= 1


def test_command_center_default(tmp_path):
    at = _run_app(tmp_path)
    assert not at.exception
    subheaders = [sh.value for sh in at.subheader]
    assert any("Coach Chat" in s for s in subheaders)
