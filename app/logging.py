from __future__ import annotations

import datetime
import logging.config
import re
from collections.abc import Mapping
from enum import IntEnum
from zoneinfo import ZoneInfo

import yaml

from app import settings


def configure_logging() -> None:
    with open("logging.yaml") as f:
        config = yaml.safe_load(f.read())
        logging.config.dictConfig(config)


class Ansi(IntEnum):
    # Default colours
    BLACK = 30
    RED = 31
    GREEN = 32
    YELLOW = 33
    BLUE = 34
    MAGENTA = 35
    CYAN = 36
    WHITE = 37

    # Light colours
    GRAY = 90
    LRED = 91
    LGREEN = 92
    LYELLOW = 93
    LBLUE = 94
    LMAGENTA = 95
    LCYAN = 96
    LWHITE = 97

    RESET = 0

    def __repr__(self) -> str:
        return f"\x1b[{self.value}m"


def get_timestamp(full: bool = False, tz: ZoneInfo | None = None) -> str:
    fmt = "%d/%m/%Y %I:%M:%S%p" if full else "%I:%M:%S%p"
    return f"{datetime.datetime.now(tz=tz):{fmt}}"


ANSI_ESCAPE_REGEX = re.compile(r"(\x9B|\x1B\[)[0-?]*[ -\/]*[@-~]")


def escape_ansi(line: str) -> str:
    return ANSI_ESCAPE_REGEX.sub("", line)


ROOT_LOGGER = logging.getLogger()


def log(
    msg: str,
    start_color: Ansi | None = None,
    extra: Mapping[str, object] | None = None,
) -> None:
    """\
    A thin wrapper around the stdlib logging module to handle mostly
    backwards-compatibility for colours during our migration to the
    standard library logging module.
    """

    # TODO: decouple colors from the base logging function; move it to
    # be a formatter-specific concern such that we can log without color.
    if start_color is Ansi.LYELLOW:
        log_level = logging.WARNING
    elif start_color is Ansi.LRED:
        log_level = logging.ERROR
    else:
        log_level = logging.INFO

    if settings.LOG_WITH_COLORS:
        color_prefix = f"{start_color!r}" if start_color is not None else ""
        color_suffix = f"{Ansi.RESET!r}" if start_color is not None else ""
    else:
        msg = escape_ansi(msg)
        color_prefix = color_suffix = ""

    ROOT_LOGGER.log(log_level, f"{color_prefix}{msg}{color_suffix}", extra=extra)


TIME_ORDER_SUFFIXES = ["nsec", "μsec", "msec", "sec"]


def magnitude_fmt_time(nanosec: int | float) -> str:
    suffix = None
    for suffix in TIME_ORDER_SUFFIXES:
        if nanosec < 1000:
            break
        nanosec /= 1000
    return f"{nanosec:.2f} {suffix}"
