from enum import Enum

class ValidationPolicy(str, Enum):
    """Defines how the system reacts to validation errors."""
    STRICT = "STRICT"
    LOG_ONLY = "LOG_ONLY"
    IGNORE = "IGNORE"