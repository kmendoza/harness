from enum import Enum


class Command(str, Enum):
    HB = "__neartbeat__"
    START = "__start__"
    STOP = "__stop__"
    PAUSE = "__pause__"
    RESUME = "__resume__"
    CONFIG = "__config__"
    KILL = "__kill__"
