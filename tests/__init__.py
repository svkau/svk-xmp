"""Test package for svk-xmp."""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path)


@pytest.fixture
def sample_image_file(temp_dir):
    """Create a sample image file for testing."""
    image_path = temp_dir / "test_image.jpg"
    # Create a minimal file (real tests would use actual image data)
    image_path.write_text("fake image data")
    return image_path


@pytest.fixture
def sample_metadata():
    """Sample metadata for testing."""
    return {
        'File:FileName': 'test.jpg',
        'File:FileSize': '1024 bytes',
        'File:ImageWidth': 800,
        'File:ImageHeight': 600,
        'EXIF:Make': 'Canon',
        'EXIF:Model': 'EOS 5D Mark IV',
        'EXIF:DateTimeOriginal': '2023:01:01 12:00:00',
        'EXIF:GPSLatitude': '59.3293',
        'EXIF:GPSLongitude': '18.0686',
        'EXIF:ISO': '100',
        'EXIF:FocalLength': '50.0 mm',
        'EXIF:ExposureTime': '1/125',
        'EXIF:FNumber': '2.8'
    }


@pytest.fixture
def mock_exiftool_wrapper():
    """Mock ExifToolWrapper for testing."""
    mock = Mock()
    mock.get_metadata.return_value = {}
    mock.set_metadata.return_value = True
    mock.remove_metadata.return_value = True
    mock.copy_metadata.return_value = True
    return mock


@pytest.fixture
def mock_metadata_processor():
    """Mock MetadataProcessor for testing."""
    mock = Mock()
    mock.extract_basic_info.return_value = {}
    mock.batch_process.return_value = []
    mock.find_files_without_metadata.return_value = []
    return mock


@pytest.fixture
def sample_directory_structure(temp_dir):
    """Create a sample directory structure with various file types."""
    # Create subdirectories
    (temp_dir / "images").mkdir()
    (temp_dir / "docs").mkdir()
    (temp_dir / "images" / "raw").mkdir()
    
    # Create sample files
    files = [
        "images/photo1.jpg",
        "images/photo2.jpeg",
        "images/photo3.png",
        "images/photo4.tiff",
        "images/raw/raw1.raw",
        "images/raw/raw2.cr2",
        "docs/readme.txt",
        "docs/manual.pdf"
    ]
    
    for file_path in files:
        full_path = temp_dir / file_path
        full_path.write_text(f"fake {file_path} content")
    
    return temp_dir


@pytest.fixture
def cli_runner():
    """Click CLI runner for testing."""
    from click.testing import CliRunner
    return CliRunner()


@pytest.fixture
def flask_app():
    """Flask app for testing."""
    from svk_xmp.web.app import create_app
    app = create_app({'TESTING': True})
    return app


@pytest.fixture
def flask_client(flask_app):
    """Flask test client."""
    return flask_app.test_client()


class TestHelpers:
    """Helper functions for tests."""
    
    @staticmethod
    def create_test_image_metadata(filename="test.jpg", **overrides):
        """Create test metadata with optional overrides."""
        base_metadata = {
            'File:FileName': filename,
            'File:FileSize': '1024 bytes',
            'File:ImageWidth': 800,
            'File:ImageHeight': 600,
            'EXIF:Make': 'Canon',
            'EXIF:Model': 'EOS 5D',
            'EXIF:DateTimeOriginal': '2023:01:01 12:00:00'
        }
        base_metadata.update(overrides)
        return base_metadata
    
    @staticmethod
    def create_minimal_metadata(filename="test.jpg"):
        """Create minimal metadata (just file info)."""
        return {
            'File:FileName': filename,
            'File:FileSize': '1024 bytes'
        }
    
    @staticmethod
    def assert_metadata_keys_present(metadata, expected_keys):
        """Assert that expected keys are present in metadata."""
        for key in expected_keys:
            assert key in metadata, f"Expected key '{key}' not found in metadata"
    
    @staticmethod
    def assert_successful_response(response, expected_status=200):
        """Assert that HTTP response is successful."""
        assert response.status_code == expected_status
        assert response.is_json
        return response.get_json()
    
    @staticmethod
    def assert_error_response(response, expected_status=400):
        """Assert that HTTP response contains error."""
        assert response.status_code == expected_status
        assert response.is_json
        data = response.get_json()
        assert 'error' in data
        return data