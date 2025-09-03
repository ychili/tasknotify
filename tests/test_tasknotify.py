import collections

import gi

try:
    gi.require_version("Notify", "0.7")
    from gi.repository import Notify
except (ImportError, ValueError):
    assert False, "libnotify not installed"

import tasknotify


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
            assert False, counters


def test_notify_headless() -> None:
    assert not Notify.is_initted()
    assert tasknotify.notify_headless(
        "Hello from the test suite!", "Content", app_name=__file__)
    assert Notify.is_initted()

