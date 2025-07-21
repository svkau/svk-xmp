"""Custom exceptions for the project."""

class MyProjectError(Exception):
    """Base exception for the project."""
    pass

class ExifToolError(MyProjectError):
    """Exception raised when exiftool operations fail."""
    pass

class ExifToolNotFoundError(MyProjectError):
    """Exception raised when exiftool is not found."""
    pass

class MetadataProcessingError(MyProjectError):
    """Exception raised during metadata processing."""
    pass