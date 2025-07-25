# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

SVK-XMP is a metadata processing tool that provides a high-level interface for working with image metadata using exiftool. The project offers both CLI and web interfaces for metadata operations.

## Development Commands

### Dependencies and Environment
```bash
# Install dependencies (requires Python 3.12+)
uv sync

# Install development dependencies
uv sync --group dev
```

### Code Quality
```bash
# Run type checking
mypy src/

# Run linting
flake8 src/

# Format code
black src/

# Run tests
pytest
```

### Running the Application
```bash
# CLI usage (after installation)
svk-xmp extract path/to/image.jpg
svk-xmp remove path/to/image.jpg --all
svk-xmp scan /path/to/directory
svk-xmp sync path/to/image.jpg --verbose
svk-xmp xmp path/to/image.jpg                    # Extract XMP in table format
svk-xmp xmp path/to/image.jpg --format raw       # Extract XMP as raw XML
svk-xmp xmp path/to/image.jpg --save output.xmp  # Save XMP packet to file
svk-xmp xmp /path/to/directory --recursive       # Process directory recursively
svk-xmp xmp /path/to/directory --save xmp_output # Save individual .xmp files for each image

# Note: ZIP files are not supported for sync operations 
# as exiftool cannot write to files within ZIP archives

# Web server (development)
python -m flask --app src.svk_xmp.web.app run
```

## Architecture

### Core Components

**ExifToolWrapper** (`core/exiftool_wrapper.py`):
- Low-level wrapper around the exiftool command-line tool
- Handles subprocess execution and error handling
- Provides methods for metadata extraction, modification, and removal
- Requires exiftool to be installed on the system

**MetadataProcessor** (`core/metadata_processor.py`):
- High-level interface for metadata operations
- Provides convenience methods like `extract_basic_info()` and `batch_process()`
- Handles common metadata field extraction with fallbacks
- Includes utility functions for finding files without metadata

**Exception Hierarchy** (`core/exceptions.py`):
- `MyProjectError`: Base exception class
- `ExifToolError`: For exiftool command failures
- `ExifToolNotFoundError`: When exiftool is not installed
- `MetadataProcessingError`: For high-level processing errors

### Interface Layers

**CLI Interface** (`cli/commands.py`):
- Click-based command-line interface
- Commands: `extract`, `remove`, `scan`, `sync`, `xmp`
- Supports both JSON and table output formats
- XMP command supports table, raw XML, and JSON formats
- Handles exiftool path configuration

**Web Interface** (`web/`):
- Flask-based REST API
- Factory pattern for app creation (`app.py`)
- Blueprint-based routing (`routes.py`)
- Health check endpoint, processing endpoint, and XMP extraction endpoints
- XMP endpoints: `/xmp` (single file) and `/xmp/batch` (multiple files)
- Supports JSON, XML, and combined format responses

### Dependencies
- **exiftool**: External dependency (must be installed separately)
- **click**: CLI framework
- **flask**: Web framework
- **requests**: HTTP client library

## Important Notes

- The project requires exiftool to be installed on the system
- All file paths are handled as `pathlib.Path` objects internally
- The project follows a layered architecture: CLI/Web → MetadataProcessor → ExifToolWrapper → exiftool binary

## Performance Optimization

The project includes persistent ExifTool process support for significant performance improvements:

- **Batch operations**: Automatically use persistent mode for directory processing (2-3x faster)
- **External scripts**: Use `MetadataProcessor(persistent=True)` for processing individual files in loops
- **Context manager**: Automatic cleanup with `with MetadataProcessor(persistent=True) as processor:`
- **Manual control**: `start_persistent_mode()` and `stop_persistent_mode()` methods

Example for external scripts processing many files individually:
```python
from svk_xmp.core.metadata_processor import MetadataProcessor

with MetadataProcessor(persistent=True) as processor:
    for image_file in my_image_files:
        xmp_xml = processor.extract_xmp_xml(image_file)  # 2-3x faster
        fields = processor.parse_xmp_fields(xmp_xml)
        # Process your data...
```

 That's a great approach! Skipping ZIP functionality for now was the right decision to get a working solution quickly, but it's definitely a valuable feature for the future.

  When you're ready to implement ZIP file support, here are the main approaches to consider:

  ## Future ZIP Implementation Options:

  Option 1: Extract → Process → Repackage
  - Extract ZIP contents to temporary directory
  - Process individual image files normally
  - Repackage into new ZIP (maintaining structure)
  - Replace original ZIP file

  Option 2: Extract → Process → Leave Extracted
  - Extract ZIP contents to destination directory
  - Process files in-place
  - Leave files extracted (don't repackage)
  - User gets processed individual files instead of ZIP

  Option 3: Dual Mode
  - Add a --extract flag to choose behavior
  - Default: Skip ZIPs with explanation
  - With flag: Extract and process according to chosen mode

  Implementation considerations for the future:
  - Preserve file timestamps and directory structure
  - Handle ZIP file permissions and metadata
  - Progress tracking for large ZIP files
  - Error handling during extraction/repackaging
  - Memory usage for large archives

  For now, the clear "not supported" message gives users a good understanding of the limitation, and the foundation is solid for adding this feature later when you have time to implement it
  properly.
  
