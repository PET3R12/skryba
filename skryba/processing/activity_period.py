from enum import Enum
from datetime import datetime


class ActivityPeriod(Enum):
    MONTH = "month"
    WEEK = "week"

    def get_date_key(self, date_obj: datetime) -> str:
        if self == ActivityPeriod.MONTH:
            return date_obj.strftime("%Y-%m")
        elif self == ActivityPeriod.WEEK:
            return f"{date_obj.isocalendar().year}-W{date_obj.isocalendar().week:02d}"
        else:
            raise ValueError(f"Unsupported period type in Enum: {self}")
