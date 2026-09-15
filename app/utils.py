from datetime import datetime
from zoneinfo import ZoneInfo

from flask import current_app


def service_timezone() -> ZoneInfo:
    """The service-wide default timezone (Asia/Seoul).

    Kept as a single function so per-user timezones (based on User.country)
    can be layered in later without touching every call site.
    """
    tz_name = current_app.config.get("DEFAULT_TIMEZONE", "Asia/Seoul")
    return ZoneInfo(tz_name)


def now_local() -> datetime:
    """Current datetime in the service timezone."""
    return datetime.now(service_timezone())


def today_local():
    """Current date in the service timezone (a plain date, no tzinfo)."""
    return now_local().date()
