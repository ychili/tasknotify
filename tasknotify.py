"""tasknotify - Headless notify"""

import argparse
import collections
import logging
import os
import sys
from collections.abc import Collection, Iterator, Sequence
from typing import TYPE_CHECKING

import gi
import psutil

try:
    gi.require_version("Notify", "0.7")
    from gi.repository import GLib, Notify
except (ImportError, ValueError):
    logging.error("libnotify not installed")
    raise

if TYPE_CHECKING:
    from _typeshed import SupportsRead

APP_NAME = "tasknotify"
NOTIFICATION_SIZE_LIMIT = 1024
REQUIRED_VARIABLES = ["DISPLAY", "DBUS_SESSION_BUS_ADDRESS"]
_VERBOSITY_LOG_LEVELS = {None: logging.WARNING, 1: logging.INFO, 2: logging.DEBUG}

logger = logging.getLogger(__name__)


def read_body_text(reader: SupportsRead[str], n: int = NOTIFICATION_SIZE_LIMIT) -> str:
    return reader.read(n).replace("\0", "").strip()


def process_environs(uid: int | None = None) -> Iterator[dict[str, str]]:
    """Yield environments of processes with real user ID *uid*.

    Default *uid* is current user.
    """
    if uid is None:
        uid = os.getuid()
    for proc in psutil.process_iter(attrs=["uids", "environ"]):
        environment = proc.info["environ"]
        if proc.info["uids"].real == uid and environment is not None:
            yield environment


def get_environ_values(*names: str) -> dict[str, collections.Counter[str]]:
    """Get Counters of values for environment variable(s) *names*.

    Scan the environments of current user processes and return counts of how
    frequently certain values occur.
    """
    values: dict[str, collections.Counter[str]] = {
        name: collections.Counter() for name in names
    }
    for environment in process_environs():
        for var, counter in values.items():
            if value := environment.get(var):
                counter[value] += 1
    return values


def _set_environ(names: Collection[str]) -> None:
    if all(os.environ.get(var) for var in names):
        logger.debug("environment variables %s already set", names)
        return
    mapping = {
        var: counter.most_common(1)[0][0]
        for var, counter in get_environ_values(*names).items()
        if counter
    }
    if not mapping:
        logger.warning(
            "unable to find environment variables in current user processes: %s", names
        )
    os.environ.update(mapping)
    logger.debug("updated environment: %s", mapping)


def notify(summary: str, body: str | None = None, app_name: str | None = None) -> bool:
    """Send libnotify notification."""
    # Docs for libnotify:
    # <https://gnome.pages.gitlab.gnome.org/libnotify/>
    if not app_name:
        # app_name cannot be '\0'.
        app_name = APP_NAME
    if not Notify.init(app_name):
        logger.error("failed to initialize libnotify with app_name: '%s'", app_name)
        return False
    notification = Notify.Notification.new(summary, body)
    notification.set_hint("desktop-entry", GLib.Variant.new_string(app_name))
    try:
        notify_result = notification.show()
    except GLib.Error as err:
        logger.error("error from libnotify: %s", err.message)
        logger.debug("error is: %s", err)
        return False
    if notify_result:
        return True
    logger.error("unknown error from libnotify")
    return False


def notify_headless(
    summary: str,
    body: str | None = None,
    app_name: str | None = None,
    session_variables: Collection[str] | None = None,
) -> bool:
    """Make a libnotify notification after setting appropriate environment.

    Returns True/False for success/failure.
    """
    if session_variables is None:
        session_variables = REQUIRED_VARIABLES
    _set_environ(session_variables)
    if body is not None:
        logger.debug("will create notification with body text: %r", body)
    return notify(summary, body, app_name)


def cla_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Send a desktop notification if there is input on standard input"
            " or if BODY is given."
        ),
        prog=APP_NAME,
    )
    parser.add_argument(
        "summary",
        metavar="SUMMARY",
        default="",
        help="produce a notification with this %(metavar)s",
    )
    parser.add_argument(
        "body",
        metavar="BODY",
        nargs="?",
        help="produce a notification with this %(metavar)s (default read from stdin)",
    )
    parser.add_argument(
        "-a", "--app-name", help=f"app name for the notification (default: {APP_NAME})"
    )
    parser.add_argument(
        "-l",
        "--limit",
        type=int,
        metavar="N",
        default=NOTIFICATION_SIZE_LIMIT,
        help=(
            "read at most %(metavar)s characters from standard input"
            " (default: %(default)d)"
        ),
    )
    parser.add_argument(
        "-v", "--verbose", action="count", help="'-vv' for debug output"
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = cla_parser().parse_args(argv)
    log_level = _VERBOSITY_LOG_LEVELS.get(args.verbose, logging.DEBUG)
    logging.basicConfig(
        format=f"{APP_NAME}: %(levelname)s: %(message)s", level=log_level
    )
    if args.body is None:
        try:
            text = read_body_text(sys.stdin, n=args.limit)
        except OSError as err:
            logger.error("unable to read from standard input: %s", err)
            return 1
        if not text:
            logger.debug("no input on standard input")
            return 0
    else:
        text = args.body
    result = notify_headless(summary=args.summary, body=text, app_name=args.app_name)
    return 0 if result else 1


if __name__ == "__main__":
    sys.exit(main())
