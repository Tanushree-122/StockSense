"""Errors that services raise for expected problems (shown to the user as a message)."""


class DomainError(Exception):
    """A business-rule problem with a message that is safe to show to the owner."""

    def __init__(self, message):
        super().__init__(message)
        self.message = message
