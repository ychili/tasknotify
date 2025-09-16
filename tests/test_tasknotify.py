from __future__ import annotations

import collections
import io
import sys
import unittest.mock

import gi
import pytest

try:
    gi.require_version("Notify", "0.7")
    from gi.repository import Notify
except (ImportError, ValueError):
    pytest.fail("libnotify not installed")

import tasknotify


@pytest.fixture(autouse=True)
def debug_messages_from_glib(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("G_MESSAGES_DEBUG", "all")


@pytest.fixture
def mock_notify(monkeypatch: pytest.MonkeyPatch) -> unittest.mock.Mock:
    """Mock a successful call to `tasknotify.notify`."""
    mocked = unittest.mock.Mock(spec=tasknotify.notify, return_value=True)
    monkeypatch.setattr(tasknotify, "notify", mocked)
    return mocked


def test_process_environs() -> None:
    environs = list(tasknotify.process_environs())
    for environ in environs:
        for key, val in environ.items():
            assert isinstance(key, str)
            assert isinstance(val, str)


def test_get_environ_values() -> None:
    counters = tasknotify.get_environ_values("HOME", "LOGNAME")
    match counters:
        case {"HOME": collections.Counter(), "LOGNAME": collections.Counter(), **extra}:
            assert not extra
        case _:
            pytest.fail(f"unexpected return value: {counters}")


@pytest.mark.parametrize("app_name", ["", "\0"])
def test_notify_invalid_app_name(app_name: str) -> None:
    assert not tasknotify.notify("Summary", "Body", app_name)


def test_notify_headless(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DISPLAY", raising=False)
    assert not Notify.is_initted()
    assert tasknotify.notify_headless(
        "Test notification", "Hello from the test suite!", app_name=__file__
    )
    assert Notify.is_initted()


def test_main_unconditional(mock_notify: unittest.mock.Mock) -> None:
    argv = "Summary", "Body"
    rc = tasknotify.main(argv)
    assert rc == 0
    mock_notify.assert_called_once_with(*argv, None)


@pytest.mark.parametrize(("text_in", "expected_body"), [("\n\n", ""), ("Body", "Body")])
def test_main_stdin(
    monkeypatch: pytest.MonkeyPatch,
    mock_notify: unittest.mock.Mock,
    text_in: str,
    expected_body: str,
) -> None:
    monkeypatch.setattr(sys, "stdin", io.StringIO(text_in))
    summary = "Summary"
    app_name = "test_tasknotify"
    rc = tasknotify.main(["--app-name", app_name, summary])
    assert rc == 0
    if expected_body:
        mock_notify.assert_called_once_with(summary, expected_body, app_name)
    else:
        mock_notify.assert_not_called()


def test_main_stdin_error_handling(monkeypatch: pytest.MonkeyPatch) -> None:
    mock_read = unittest.mock.Mock(spec=tasknotify.read_body_text, side_effect=IOError)
    monkeypatch.setattr(tasknotify, "read_body_text", mock_read)
    rc = tasknotify.main(["Summary"])
    assert rc > 0
    mock_read.assert_called_once()
