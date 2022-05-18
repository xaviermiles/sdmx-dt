from datetime import date
from enum import Enum, auto


class FacetValueType(Enum):
    # TODO: fill in auto() values with Python data types
    STRING = str
    BIG_INTEGER = int
    INTEGER = int
    LONG = int
    SHORT = int
    DECIMAL = auto()
    FLOAT = auto()
    DOUBLE = auto()
    BOOLEAN = auto()
    URI = auto()
    COUNT = auto()
    INCLUSIVE_VALUE_RANGE = auto()
    ALPHA = auto()
    ALPHA_NUMERIC = auto()
    NUMERIC = auto()
    EXCLUSIVE_VALUE_RANGE = auto()
    INCREMENTAL = auto()
    OBSERVATIONAL_TIME_PERIOD = auto()
    STANDARD_TIME_PERIOD = auto()
    BASIC_TIME_PERIOD = auto()
    GREGORIAN_TIME_PERIOD = auto()
    GREGORIAN_YEAR_MONTH = auto()
    GREGORIAN_DAY = auto()
    REPORTING_TIME_PERIOD = auto()
    REPORTING_YEAR = auto()
    REPORTING_SEMESTER = auto()
    REPORTING_TRIMESTER = auto()
    REPORTING_QUARTER = auto()
    REPORTING_MONTH = auto()
    REPORTING_WEEK = auto()
    REPORTING_DAY = auto()
    DATE_TIME = auto()
    TIMES_RANGE = auto()
    MONTH = auto()
    MONTH_DAY = auto()
    DAY = auto()
    TIME = auto()
    DURATION = auto()
    KEY_VALUES = auto()
    IDENTIFIABLE_REFERENCE = auto()
    DATA_SET_REFERENCE = auto()


# Can't directly extend Enum which has members
ExtendedFacetValueType = Enum("ExtendedFacetValueType", {**FacetValueType, "XHTML": str})  # type: ignore


class FacetType(Enum):
    # TODO: are these supposed to be referencing FacetValueType or Python types?
    IS_SEQUENCE = FacetValueType.BOOLEAN
    MIN_LENGTH = FacetValueType.INTEGER  # positiveInteger
    MAX_LENGTH = FacetValueType.INTEGER  # positiveInteger
    MIN_VALUE = FacetValueType.DECIMAL
    MAX_VALUE = FacetValueType.DECIMAL
    END_VALUE = FacetValueType.STRING
    INTERVAL = FacetValueType.DOUBLE
    TIME_INTERVAL = FacetValueType.DURATION
    DECIMALS = FacetValueType.INTEGER  # positiveInteger
    PATTERN = FacetValueType.STRING
    START_TIME = date
    END_TIME = date


class UsageStatus(Enum):
    MANDATORY = str
    CONDITIONAL = str


class ActionType(Enum):
    DELETE = str
    REPLACE = str
    APPEND = str
    INFORMATION = str


class ToValueType(Enum):
    NAME = str
    DESCRIPTION = str
    ID = str


class ConstraintRoleType(Enum):
    ALLOWABLE_CONTENT = str
    ACTUAL_CONTENT = str
