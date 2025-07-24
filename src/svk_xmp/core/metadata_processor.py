"""High-level metadata processing functionality."""

from pathlib import Path
from typing import Dict, List, Optional, Union, Callable, Any
from .exiftool_wrapper import ExifToolWrapper
from .exceptions import MetadataProcessingError


class MetadataProcessor:
    """High-level interface for metadata operations."""

    def __init__(self, exiftool_path: Optional[str] = None, persistent: bool = False):
        """Initialize with optional custom exiftool path and persistent mode."""
        self.persistent = persistent
        self.exiftool_path = exiftool_path
        
        if persistent:
            self.exiftool = ExifToolWrapper(exiftool_path, persistent=True)
        else:
            self.exiftool = ExifToolWrapper(exiftool_path)

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - cleanup persistent process if needed."""
        if self.persistent and hasattr(self.exiftool, '_stop_persistent_process'):
            self.exiftool._stop_persistent_process()

    def start_persistent_mode(self):
        """Manually start persistent mode if not already active."""
        if not self.persistent:
            self.exiftool = ExifToolWrapper(self.exiftool_path, persistent=True)
            self.persistent = True

    def stop_persistent_mode(self):
        """Manually stop persistent mode."""
        if self.persistent and hasattr(self.exiftool, '_stop_persistent_process'):
            self.exiftool._stop_persistent_process()
            self.exiftool = ExifToolWrapper(self.exiftool_path, persistent=False)
            self.persistent = False

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

    def sync_metadata(
        self, 
        path: Union[str, Path], 
        args_file: Union[str, Path] = "arg_files/metadata_sync_images.args",
        file_extensions: Optional[List[str]] = None,
        recursive: bool = True,
        verbose: bool = False,
        progress_callback: Optional[Callable[[str, int, int], None]] = None
    ) -> Dict[str, Any]:
        """
        Synchronize metadata between EXIF, IPTC, and XMP formats in image files.
        
        This is a high-level interface to the ExifToolWrapper.sync_metadata method.
        
        Args:
            path: File, directory, or zip file to process
            args_file: Path to exiftool arguments file for metadata synchronization
            file_extensions: List of file extensions to process (e.g., ['.jpg', '.jpeg'])
            recursive: Include subdirectories when processing directories
            verbose: Enable detailed output messages
            progress_callback: Optional callback function (current_file, current_index, total_files)
            
        Returns:
            Dictionary with processing results including processed files, errors, warnings, and summary
            
        Raises:
            MetadataProcessingError: If there are issues with the processing operation
        """
        try:
            return self.exiftool.sync_metadata(
                path=path,
                args_file=args_file,
                file_extensions=file_extensions,
                recursive=recursive,
                verbose=verbose,
                progress_callback=progress_callback
            )
        except Exception as e:
            raise MetadataProcessingError(f"Failed to sync metadata: {str(e)}")

    def extract_xmp_xml(self, file_path: Union[str, Path]) -> str:
        """Extract clean XMP XML from a file."""
        try:
            return self.exiftool.extract_xmp_xml(file_path)
        except Exception as e:
            raise MetadataProcessingError(f"Failed to extract XMP: {str(e)}")

    def extract_xmp_packet(self, file_path: Union[str, Path]) -> str:
        """Extract full XMP packet from a file."""
        try:
            return self.exiftool.extract_xmp_packet(file_path)
        except Exception as e:
            raise MetadataProcessingError(f"Failed to extract XMP packet: {str(e)}")

    def parse_xmp_fields(self, xmp_xml: str) -> Dict[str, str]:
        """Parse key XMP fields for tabular display."""
        if not xmp_xml:
            return {}
        
        import xml.etree.ElementTree as ET
        import re
        
        fields = {
            'title': '',
            'description': '',
            'date_created': '',
            'creator': '',
            'keywords': ''
        }
        
        try:
            # Parse XML
            root = ET.fromstring(xmp_xml)
            
            # Define namespaces
            namespaces = {
                'rdf': 'http://www.w3.org/1999/02/22-rdf-syntax-ns#',
                'dc': 'http://purl.org/dc/elements/1.1/',
                'xmp': 'http://ns.adobe.com/xap/1.0/',
                'photoshop': 'http://ns.adobe.com/photoshop/1.0/'
            }
            
            # Find Description elements
            descriptions = root.findall('.//rdf:Description', namespaces)
            
            for desc in descriptions:
                # Title (dc:title)
                title_elem = desc.find('.//dc:title/rdf:Alt/rdf:li', namespaces)
                if title_elem is not None and title_elem.text:
                    fields['title'] = title_elem.text
                
                # Description (dc:description)
                desc_elem = desc.find('.//dc:description/rdf:Alt/rdf:li', namespaces)
                if desc_elem is not None and desc_elem.text:
                    fields['description'] = desc_elem.text
                
                # Date Created (xmp:CreateDate or photoshop:DateCreated)
                date_elem = desc.find('.//xmp:CreateDate', namespaces)
                if date_elem is None:
                    date_elem = desc.find('.//photoshop:DateCreated', namespaces)
                if date_elem is not None and date_elem.text:
                    fields['date_created'] = date_elem.text
                
                # Creator (dc:creator)
                creator_elem = desc.find('.//dc:creator/rdf:Seq/rdf:li', namespaces)
                if creator_elem is not None and creator_elem.text:
                    fields['creator'] = creator_elem.text
                
                # Keywords (dc:subject)
                keywords = []
                keyword_elems = desc.findall('.//dc:subject/rdf:Bag/rdf:li', namespaces)
                for kw_elem in keyword_elems:
                    if kw_elem.text:
                        keywords.append(kw_elem.text)
                if keywords:
                    fields['keywords'] = ', '.join(keywords)
        
        except ET.ParseError:
            # If XML parsing fails, return empty fields
            pass
        
        return fields

    def batch_extract_xmp(
        self, 
        path: Union[str, Path], 
        recursive: bool = False,
        progress_callback: Optional[Callable[[str, int, int], None]] = None,
        use_persistent: bool = True
    ) -> Dict[str, Any]:
        """Batch XMP extraction with progress tracking and optional persistent mode."""
        path = Path(path)
        
        # Initialize result structure similar to sync_metadata
        result = {
            'processed': [],
            'errors': [],
            'skipped': [],
            'summary': {
                'total_files': 0,
                'processed': 0,
                'errors': 0,
                'skipped': 0
            }
        }
        
        # Get list of files to process
        file_extensions = ['.jpg', '.jpeg', '.jpe', '.tif', '.tiff', '.png', '.gif', '.bmp', '.webp']
        files_to_process = self.exiftool._get_files_to_process(path, file_extensions, recursive)
        result['summary']['total_files'] = len(files_to_process)
        
        # Filter out unsupported files first
        valid_files = []
        for file_path in files_to_process:
            if file_path.suffix.lower() == '.zip':
                result['skipped'].append({
                    'file': str(file_path),
                    'reason': 'ZIP files not supported'
                })
                result['summary']['skipped'] += 1
                continue
            
            if file_path.suffix.lower() not in file_extensions:
                result['skipped'].append({
                    'file': str(file_path),
                    'reason': 'Unsupported file type'
                })
                result['summary']['skipped'] += 1
                continue
            
            valid_files.append(file_path)
        
        if not valid_files:
            return result
        
        # Use persistent mode for batch processing if requested and we have multiple files
        if use_persistent and len(valid_files) > 1:
            with ExifToolWrapper(self.exiftool.exiftool_path, persistent=True) as persistent_wrapper:
                # Batch extract XMP XML from all files
                xmp_results = persistent_wrapper.batch_extract_xmp_xml(valid_files)
                
                # Process results
                for index, file_path in enumerate(valid_files):
                    if progress_callback:
                        progress_callback(str(file_path), index, len(valid_files))
                    
                    try:
                        xmp_xml = xmp_results.get(str(file_path), "")
                        
                        if not xmp_xml:
                            result['skipped'].append({
                                'file': str(file_path),
                                'reason': 'No XMP metadata found'
                            })
                            result['summary']['skipped'] += 1
                            continue
                        
                        # Parse fields
                        fields = self.parse_xmp_fields(xmp_xml)
                        
                        result['processed'].append({
                            'file': str(file_path),
                            'xmp_xml': xmp_xml,
                            'fields': fields
                        })
                        result['summary']['processed'] += 1
                        
                    except Exception as e:
                        result['errors'].append({
                            'file': str(file_path),
                            'error': str(e)
                        })
                        result['summary']['errors'] += 1
        else:
            # Process files individually (non-persistent mode or single file)
            for index, file_path in enumerate(valid_files):
                if progress_callback:
                    progress_callback(str(file_path), index, len(valid_files))
                
                try:
                    # Extract XMP
                    xmp_xml = self.extract_xmp_xml(file_path)
                    if not xmp_xml:
                        result['skipped'].append({
                            'file': str(file_path),
                            'reason': 'No XMP metadata found'
                        })
                        result['summary']['skipped'] += 1
                        continue
                    
                    # Parse fields
                    fields = self.parse_xmp_fields(xmp_xml)
                    
                    result['processed'].append({
                        'file': str(file_path),
                        'xmp_xml': xmp_xml,
                        'fields': fields
                    })
                    result['summary']['processed'] += 1
                    
                except Exception as e:
                    result['errors'].append({
                        'file': str(file_path),
                        'error': str(e)
                    })
                    result['summary']['errors'] += 1
        
        return result