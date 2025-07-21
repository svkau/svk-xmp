"""Public API for library usage."""

from .core.metadata_processor import MetadataProcessor
from .core.exiftool_wrapper import ExifToolWrapper
from .core.exceptions import MyProjectError, ExifToolError, ExifToolNotFoundError

__version__ = "0.1.0"
__all__ = ['MetadataProcessor', 'ExifToolWrapper', 'MyProjectError', 'ExifToolError', 'ExifToolNotFoundError']