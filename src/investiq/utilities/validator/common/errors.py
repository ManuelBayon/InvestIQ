# ---------------------------------------------------------------------------
#                               Exceptions
# ---------------------------------------------------------------------------
class ValidationError(Exception):
    """Base class for all validation-related exceptions."""
    pass

class RecoverableValidationError(ValidationError):
    """An error that can be retried or logged without halting the pipeline."""
    pass

class NonRecoverableValidationError(ValidationError):
    """An error that must abort the current operation."""
    pass