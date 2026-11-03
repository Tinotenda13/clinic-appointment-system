
from abc import ABC, abstractmethod


class Clock(ABC):

    @abstractmethod
    def now(self):
        pass


class FakeClock(Clock):

    def __init__(self, current_hour):
        self.set_time(current_hour)

    def now(self):
        return self.__current_hour

    def set_time(self, new_hour):
        if not isinstance(new_hour, int):
            raise ValueError("Time must be a whole number.")

        if new_hour < 0 or new_hour > 168:
            raise ValueError("Time must be between 0 and 168.")

        self.__current_hour = new_hour
