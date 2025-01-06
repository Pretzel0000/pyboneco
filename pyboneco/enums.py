from enum import IntEnum


class AuthState(IntEnum):
    AUTH_ERROR = -1
    GOT_NONCE = 0
    CONFIRM_WAITING = 1
    CONFIRMED = 2
    GOT_DEVICE_KEY = 3
    AUTH_SUCCESS = 9


class OperationMode(IntEnum):
    NONE = 0
    HUMIDIFIER = 1
    PURIFIER = 2
    HYBRID = 3


class ModeStatus(IntEnum):
    CUSTOM = 0
    AUTO = 1
    BABY = 2
    SLEEP = 3


class TimerStatus(IntEnum):
    OFF = 0
    ACTIVE_OFF = 1
    ACTIVE_ON = 2
    RESERVED = 3
