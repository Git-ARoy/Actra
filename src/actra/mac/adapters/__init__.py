"""Concrete application adapters for Actra."""

from .safari_adapter import SafariAdapter
from .filesystem_adapter import FilesystemAdapter
from .noop_adapter import NoOpAdapter

__all__ = [
    "SafariAdapter",
    "FilesystemAdapter",
    "NoOpAdapter",
]
