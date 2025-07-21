"""High-level metadata processing functionality."""

from pathlib import Path
from typing import Dict, List, Optional, Union
from .exiftool_wrapper import ExifToolWrapper
from .exceptions import MetadataProcessingError


class MetadataProcessor:
    """High-level interface for metadata operations."""

    def __init__(self, exiftool_path: Optional[str] = None):
        """Initialize with optional custom exiftool path."""
        self.exiftool = ExifToolWrapper(exiftool_path)

    def extract_basic_info(self, file_path: Union[str, Path]) -> Dict:
        """Extract commonly used metadata fields."""
        metadata = self.exiftool.get_metadata(file_path)

        # Extract common fields with fallbacks
        basic_info = {
            'filename': Path(file_path).name,
            'file_size': metadata.get('File:FileSize', 'Unknown'),
            'image_width': metadata.get('File:ImageWidth', metadata.get('EXIF:ImageWidth')),
            'image_height': metadata.get('File:ImageHeight', metadata.get('EXIF:ImageHeight')),
            'camera_make': metadata.get('EXIF:Make'),
            'camera_model': metadata.get('EXIF:Model'),
            'date_taken': metadata.get('EXIF:DateTimeOriginal', metadata.get('EXIF:DateTime')),
            'gps_latitude': metadata.get('EXIF:GPSLatitude'),
            'gps_longitude': metadata.get('EXIF:GPSLongitude'),
        }

        return {k: v for k, v in basic_info.items() if v is not None}

    def batch_process(self, file_paths: List[Union[str, Path]],
                      operation: str, **kwargs) -> List[Dict]:
        """Process multiple files in batch."""
        results = []

        for file_path in file_paths:
            try:
                if operation == "extract":
                    result = self.extract_basic_info(file_path)
                elif operation == "remove":
                    tags = kwargs.get('tags')
                    success = self.exiftool.remove_metadata(file_path, tags)
                    result = {'file': str(file_path), 'success': success}
                else:
                    raise MetadataProcessingError(f"Unknown operation: {operation}")

                results.append(result)

            except Exception as e:
                results.append({
                    'file': str(file_path),
                    'error': str(e)
                })

        return results

    def find_files_without_metadata(self, directory: Union[str, Path],
                                    extensions: Optional[List[str]] = None) -> List[Path]:
        """Find files in directory that lack metadata."""
        directory = Path(directory)
        extensions = extensions or ['.jpg', '.jpeg', '.png', '.tiff', '.raw']

        files_without_metadata = []

        for ext in extensions:
            for file_path in directory.rglob(f"*{ext}"):
                try:
                    metadata = self.exiftool.get_metadata(file_path)
                    if not metadata or len(metadata) <= 2:  # Only basic file info
                        files_without_metadata.append(file_path)
                except Exception:
                    continue

        return files_without_metadata

    def backup_pdf_metadata(self, pdf_path: Union[str, Path]) -> str:
        """Create XML backup of all PDF metadata."""
        return self.exiftool.backup_metadata_to_xml_string(pdf_path)

    def restore_pdf_metadata(self, xml_backup: str, pdf_path: Union[str, Path]) -> bool:
        """Restore PDF metadata from XML backup."""
        return self.exiftool.restore_metadata_from_xml_string(xml_backup, pdf_path)