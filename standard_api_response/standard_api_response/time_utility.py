from enum import Enum, auto
from datetime import datetime

class ChronoType(Enum):
    MS = auto()
    SEC = auto()
    MIN = auto()
    HOUR = auto()
    DAY = auto()
    WEEK = auto()
    MONTH = auto()
    YEAR = auto()


def time_diff(start_time, end_time, unit=ChronoType.MS):
    if not isinstance(start_time, datetime) or not isinstance(end_time, datetime):
        raise ValueError("start_time and end_time must be datetime objects")

    _timedelta = end_time - start_time

    result = _timedelta.total_seconds() * 1000 if unit == ChronoType.MS \
        else _timedelta.total_seconds() if unit == ChronoType.SEC \
        else _timedelta.total_seconds() / 60 if unit == ChronoType.MIN \
        else _timedelta.total_seconds() / 3600 if unit == ChronoType.HOUR \
        else _timedelta.days if unit == ChronoType.DAY \
        else _timedelta.days / 7 if unit == ChronoType.WEEK \
        else end_time.month - start_time.month if unit == ChronoType.MONTH \
        else end_time.year - start_time.year if unit == ChronoType.YEAR \
        else 0

    return int(result)
