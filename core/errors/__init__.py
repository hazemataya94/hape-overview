"""Centralized error classes and handlers for HAPE."""

from core.errors.exceptions import HapeError, HapeExternalError, HapeOperationError, HapeUserAbortError, HapeValidationError
from core.errors.handler import ErrorHandler

__all__ = [
    "ErrorHandler",
    "HapeError",
    "HapeExternalError",
    "HapeOperationError",
    "HapeUserAbortError",
    "HapeValidationError",
]


if __name__ == "__main__":
    print(__all__)
