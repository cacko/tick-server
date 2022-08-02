from app.lametric.models import (
    TimeFrame,
    GoalData,
    DateFrame,
)
from datetime import datetime
from pandas import Period


class ClockMeta(type):

    _instance = None

    def __call__(self, *args, **kwds):
        if not self._instance:
            self._instance = super().__call__(*args, **kwds)
        return self._instance


class Clock(object, metaclass=ClockMeta):

    ICON_1 = 11543

    __last_called: str = ''
    __icon = 3265

    @property
    def time(self):
        return datetime.now().strftime('%H:%M')

    @property
    def date(self):
        return datetime.now().strftime('%a %d %B %Y')

    @property
    def date_icon(self):
        d = datetime.now().day
        return self.ICON_1 + (d - 1)

    @property
    def week_day(self):
        d = datetime.now()
        return int(d.strftime("%w"))

    @property
    def month_day(self):
        d = datetime.now()
        return int(d.strftime("%d"))

    @property
    def days_in_month(self):
        d = datetime.now().date()
        return Period(d.isoformat()).days_in_month

    @property
    def icon(self):
        return self.__icon

    @icon.setter
    def icon(self, val):
        self.__icon = val

    @property
    def isUpdated(self):
        if self.time != self.__last_called:
            return True
        return False

    def getFrames(self):
        time = self.time
        date = self.date
        self.__last_called = time
        return [
            TimeFrame(
                text=f"{time}",
                icon=self.icon,
                duration=10000,
                goalData=GoalData(start=0, end=6, current=self.week_day),
            ),
            DateFrame(
                text=date,
                icon=self.date_icon,
                goalData=GoalData(start=1, end=self.days_in_month, current=self.month_day)
            ),
        ]
