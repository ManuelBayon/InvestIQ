

class Errors:
    # start()
    START_ALREADY_STARTED = "start() not allowed: already started"
    START_ALREADY_ENDED = "start() not allowed: already ended"

    # write()
    WRITE_IN_NEW_STATE = "write() not allowed: current state: new, must be: started"
    WRITE_ALREADY_ENDED = "write() not allowed: current state: new, must be: ended"
    BATCH_WRITE_ONLY_ONCE = "write ()not allowed: BatchGuardedWriter can only write once"

    # end()
    END_ALREADY_ENDED = "end() not allowed: already ended"

    # on_write()
    CORE_WRITE_FAILED = "on_write() failed: core error"

    # validate()
    VALIDATE_FAILED = "validate() failed"

class ExportError(Exception):
    """Base exception for all export-related errors."""
    def __init__(
            self,
            message: str, *,
            context: dict[str, object] | None = None
    ):
        super().__init__(message)
        self.context = context or {}

class ExportCommitError(ExportError):
    """Raises when the sink fails"""
    pass

