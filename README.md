# SVK-XMP

A metadata processing tool that provides a high-level interface for working with image metadata using exiftool. SVK-XMP offers both CLI and web interfaces for comprehensive metadata operations including extraction, removal, scanning, and synchronization.

## Features

- **Extract metadata** from images in various formats
- **Extract XMP metadata** with support for Dublin Core fields (Title, Description, Creator, Keywords, Date Created)
- **Remove metadata** selectively or completely
- **Scan directories** for files lacking metadata
- **Synchronize metadata** between EXIF, IPTC, and XMP formats
- **Multiple interfaces**: Command-line, Python library, and web API
- **Batch processing** with progress tracking and detailed reporting
- **File validation** using exiftool's built-in validation
- **Flexible output formats** (JSON, table, raw XML, summary)

## Prerequisites

- **Python 3.12+**
- **exiftool** must be installed on your system
  - macOS: `brew install exiftool`
  - Ubuntu/Debian: `sudo apt-get install libimage-exiftool-perl`
  - Windows: Download from [exiftool.org](https://exiftool.org/)

## Installation

### From Source

```bash
# Clone the repository
git clone <repository-url>
cd svk-xmp

# Install with uv (recommended)
uv sync
uv pip install -e .

# Or with pip
pip install -e .
```

## Usage

### Command Line Interface

```bash
# Extract metadata from a single image
svk-xmp extract path/to/image.jpg

# Extract metadata in JSON format
svk-xmp extract path/to/image.jpg --format json

# Remove all metadata from an image
svk-xmp remove path/to/image.jpg --all

# Remove specific metadata tags
svk-xmp remove path/to/image.jpg --tags EXIF:Make --tags EXIF:Model

# Scan directory for files without metadata
svk-xmp scan /path/to/directory

# Synchronize metadata between EXIF, IPTC, and XMP
svk-xmp sync path/to/image.jpg --verbose
svk-xmp sync /path/to/directory --recursive
svk-xmp sync /path/to/images --extensions .jpg --extensions .tiff

# Extract XMP metadata
svk-xmp xmp path/to/image.jpg                    # Table format (default)
svk-xmp xmp path/to/image.jpg --format raw       # Raw XML output
svk-xmp xmp path/to/image.jpg --format json      # JSON output
svk-xmp xmp path/to/image.jpg --save output.xmp  # Save XMP packet to file
svk-xmp xmp /path/to/directory --recursive       # Process directory recursively
svk-xmp xmp /path/to/directory --save xmp_files  # Save individual .xmp files for each image

# Custom exiftool path
svk-xmp --exiftool-path /custom/path/exiftool extract image.jpg
```

### Python Library

```python
from svk_xmp import MetadataProcessor

# Initialize processor
processor = MetadataProcessor()

# Extract basic metadata information
metadata = processor.extract_basic_info('image.jpg')
print(metadata)

# Synchronize metadata formats
result = processor.sync_metadata(
    path='/path/to/images',
    recursive=True,
    verbose=True
)
print(f"Processed: {result['summary']['processed']} files")

# Scan for files without metadata
files = processor.find_files_without_metadata('/path/to/directory')

# Extract XMP metadata
xmp_xml = processor.extract_xmp_xml('image.jpg')
xmp_packet = processor.extract_xmp_packet('image.jpg')  # Includes <?xpacket> declarations

# Parse XMP fields for display
fields = processor.parse_xmp_fields(xmp_xml)
print(f"Title: {fields['title']}")
print(f"Creator: {fields['creator']}")
print(f"Keywords: {fields['keywords']}")

# Batch XMP extraction
result = processor.batch_extract_xmp('/path/to/directory', recursive=True)
print(f"Found XMP data in {result['summary']['processed']} files")

# For external scripts processing many individual files - use persistent mode
with MetadataProcessor(persistent=True) as processor:
    for image_file in my_image_files:
        xmp_xml = processor.extract_xmp_xml(image_file)  # Much faster!
        fields = processor.parse_xmp_fields(xmp_xml)
        # Process your data...

# Or manual control
processor = MetadataProcessor()
processor.start_persistent_mode()
try:
    for image_file in my_image_files:
        xmp_xml = processor.extract_xmp_xml(image_file)  # Much faster!
        # Process your data...
finally:
    processor.stop_persistent_mode()
```

### Web API

```bash
# Start the web server
svk-xmp serve --host 0.0.0.0 --port 5000

# Or using Flask directly
python -m flask --app src.svk_xmp.web.app run
```

API endpoints:
- `GET /` - Health check
- `POST /process` - Process metadata operations
- `GET /xmp?file=path&format=json|xml|both` - Extract XMP from single file
- `POST /xmp/batch` - Batch XMP extraction with JSON payload: `{"path": "/dir", "recursive": true, "format": "json"}`

## Metadata Synchronization

The sync functionality harmonizes metadata across different formats:

- **EXIF → IPTC**: Artist, Copyright, Image Description, DateTime
- **EXIF → XMP**: Complete EXIF data plus enhanced XMP fields
- **IPTC → XMP**: Keywords, Titles, Descriptions, Location data

### Sync Features

- **File validation** before processing
- **Batch processing** with detailed progress reporting
- **Error handling** continues processing other files on individual failures
- **Flexible file filtering** by extension
- **Directory recursion** control
- **Custom argument files** for specialized sync operations

### Example Sync Output

```bash
$ svk-xmp sync /photos --verbose

Found 150 files to process
Processed: /photos/IMG_001.jpg
Processed: /photos/IMG_002.jpg
Warning in /photos/IMG_003.jpg: Missing GPS data
...

Metadata synchronization completed:
  Total files: 150
  Processed: 148
  Errors: 0
  Warnings: 12
  Skipped: 2
```

## XMP Metadata Extraction

The XMP extraction functionality provides comprehensive access to XMP metadata embedded in images, with support for Dublin Core and other XMP namespaces.

### Supported XMP Fields

The parser extracts key Dublin Core fields commonly used in image metadata:

- **Title** (`dc:title`): Image title or heading
- **Description** (`dc:description`): Image description or caption  
- **Creator** (`dc:creator`): Image creator or author
- **Keywords** (`dc:subject`): Comma-separated keywords/tags
- **Date Created** (`xmp:CreateDate` or `photoshop:DateCreated`): Creation timestamp

### XMP Output Formats

1. **Table format** (default): Human-readable key-value pairs showing populated fields
2. **Raw XML format**: Clean XMP XML suitable for integration into XML documents  
3. **JSON format**: Structured data with both parsed fields and raw XML
4. **Save to file**: Full XMP packet with `<?xpacket>` declarations for .xmp files

### Saving XMP Files

The `--save` option behavior depends on the input:

- **Single file**: `svk-xmp xmp photo.jpg --save metadata.xmp` → saves to `metadata.xmp`
- **Directory**: `svk-xmp xmp photos/ --save xmp_output` → creates `xmp_output/` directory with individual `.xmp` files for each image:
  - `photos/IMG_001.jpg` → `xmp_output/IMG_001.xmp`
  - `photos/IMG_002.jpg` → `xmp_output/IMG_002.xmp`
  - etc.

The output directory is created automatically if it doesn't exist.

### Example XMP Output

**Table format:**
```bash
$ svk-xmp xmp photo.jpg

File: photo.jpg
===============
Title          : Summer Sunset
Description    : Beautiful sunset over the ocean
Creator        : John Photographer  
Keywords       : sunset, ocean, landscape
Date Created   : 2023-07-15T19:30:00Z
```

**Raw XML format:**
```bash
$ svk-xmp xmp photo.jpg --format raw

<x:xmpmeta xmlns:x='adobe:ns:meta/'>
<rdf:RDF xmlns:rdf='http://www.w3.org/1999/02/22-rdf-syntax-ns#'>
 <rdf:Description rdf:about=''
  xmlns:dc='http://purl.org/dc/elements/1.1/'>
  <dc:title>
   <rdf:Alt>
    <rdf:li xml:lang='x-default'>Summer Sunset</rdf:li>
   </rdf:Alt>
  </dc:title>
 </rdf:Description>
</rdf:RDF>
</x:xmpmeta>
```

## Limitations

- **ZIP files**: Currently not supported for sync operations as exiftool cannot write to files within ZIP archives
- **Write permissions**: Requires write access to image files for sync and remove operations
- **Large files**: Processing very large images may require significant memory

## Development

### Setup Development Environment

```bash
# Install with development dependencies
uv sync --group dev

# Run tests
pytest

# Code formatting
black src/

# Type checking
mypy src/

# Linting
flake8 src/
```

### Architecture

The project follows a layered architecture:

```
CLI/Web → MetadataProcessor → ExifToolWrapper → exiftool binary
```

- **ExifToolWrapper**: Low-level wrapper around exiftool commands
- **MetadataProcessor**: High-level interface with convenience methods  
- **CLI/Web**: User-facing interfaces

### Project Structure

```
src/svk_xmp/
├── cli/                    # Command-line interface
│   └── commands.py
├── core/                   # Core functionality
│   ├── exiftool_wrapper.py # Low-level exiftool interface
│   ├── metadata_processor.py # High-level processing
│   └── exceptions.py       # Custom exceptions
└── web/                    # Web API
    ├── app.py
    └── routes.py
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes with tests
4. Ensure all tests pass: `pytest`
5. Submit a pull request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

The MIT License allows you to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of this software for any purpose, including commercial applications, with the only requirement being to include the copyright notice and license text.

## Changelog

### Latest Features
- ✅ **XMP metadata extraction** with Dublin Core field parsing (Title, Description, Creator, Keywords, Date Created)
- ✅ **Multiple XMP output formats**: Table view, raw XML, JSON, and save to .xmp files
- ✅ **Batch XMP processing** with recursive directory support
- ✅ **XMP Web API endpoints** for single file and batch operations
- ✅ Metadata synchronization between EXIF, IPTC, and XMP
- ✅ Comprehensive CLI interface with all sync options
- ✅ File validation and error handling
- ✅ Batch processing with progress tracking
- ✅ Web API interface

### Upcoming
- 🔄 ZIP file extraction and processing
- 🔄 Additional metadata format support
- 🔄 Configuration file support