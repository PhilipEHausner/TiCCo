from __future__ import annotations
from typing import Optional
import re


class Timestamp:
    """
    Storage object for timestamps, specifying them as a combination of year, month and day.
    """
    year: Optional[int]
    month: Optional[int]
    day: Optional[int]
    granularity: str

    # invalid values in a tag for creation of a timestamp, we only accept years AD for now
    invalid_tags = ["REF", "BC"]

    # This pattern finds the correct date tag in a TIMEX3 tag (value states the actual date)
    tag_pattern = re.compile(r"value=[\"'](.*?)[\"']")

    def __init__(self, year: int = None, month: int = None, day: int = None) -> None:
        """
        When params are explicitly provided. Does not range checks.
        @param year: year
        @param month: month
        @param day: day
        """
        try:
            self.year = None
            self.month = None
            self.day = None
            if year:
                self.year = year
                if month:
                    self.month = month
                    if day:
                        self.day = day
            if day:
                self.granularity = "D"
            elif month:
                self.granularity = "M"
            elif year:
                self.granularity = "Y"
            else:
                self.granularity = "NONE"
        except Exception as e:
            print("Timestamp constructor:", e)

    @classmethod
    def from_HeidelTimeTag(cls, tag: str) -> Timestamp:
        """
        Parses a TIMEX3 tag and creates a timestamp out of it.
        @param tag:
        @return:
        """
        try:
            datestring = re.search(cls.tag_pattern, tag).group(1)
        except Exception as e:
            return cls()

        for item in cls.invalid_tags:
            if item in datestring:
                return cls()

        year = None
        month = None
        day = None

        date = datestring.split("-")

        if len(date) > 0:
            if date[0].isnumeric() and len(date[0]) == 4:
                year = int(date[0])
                if len(date) > 1:
                    if date[1].isnumeric() and len(date[1]) == 2:
                        month = int(date[1])
                        if len(date) > 2:
                            if date[2].isnumeric() and len(date[2]) == 2:
                                day = int(date[2])

        return cls(year, month, day)

    def __repr__(self):
        return "Timestamp({0}, {1}, {2})".format(self.year, self.month, self.day)

    def __str__(self):
        if self.day:
            return "{:04d}-{:02d}-{:02d}".format(self.year, self.month, self.day)
        elif self.month:
            return "{:04d}-{:02d}".format(self.year, self.month)
        elif self.year:
            return "{:04d}".format(self.year)
        else:
            return ""

    def __eq__(self, other):
        if isinstance(other, Timestamp):
            return (self.day, self.month, self.year) == (other.day, other.month, other.year)
        return NotImplemented

    def __hash__(self):
        return hash((self.year, self.month, self.day))
