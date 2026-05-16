from enum import Enum


class PopularityLevel(Enum):
    LOW = "Low popularity"
    MODERATE = "Moderate popularity"
    AVERAGE = "Average popularity"
    HIGH = "High popularity"
    VERY_HIGH = "Very high popularity"

    @classmethod
    def from_score(cls, score: int) -> "PopularityLevel":
        if score < 40:
            return cls.LOW
        elif score < 200:
            return cls.MODERATE
        elif score < 600:
            return cls.AVERAGE
        elif score < 2000:
            return cls.HIGH
        else:
            return cls.VERY_HIGH
