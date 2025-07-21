"""Tests for core functionality."""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import json
import subprocess

from svk_xmp.core.exiftool_wrapper import ExifToolWrapper
from svk_xmp.core.metadata_processor import MetadataProcessor
from svk_xmp.core.exceptions import (
    ExifToolError,
    ExifToolNotFoundError,
    MetadataProcessingError
)


class TestExifToolWrapper:
    """Test ExifToolWrapper functionality."""

    def test_init_with_custom_path(self):
        """Test initialization with custom exiftool path."""
        with patch('shutil.which', return_value='/custom/path/exiftool'):
            wrapper = ExifToolWrapper('/custom/path/exiftool')
            assert wrapper.exiftool_path == '/custom/path/exiftool'

    def test_init_with_default_path(self):
        """Test initialization with default exiftool path."""
        with patch('shutil.which', return_value='/usr/bin/exiftool'):
            wrapper = ExifToolWrapper()
            assert wrapper.exiftool_path == 'exiftool'

    def test_init_exiftool_not_found(self):
        """Test initialization when exiftool is not found."""
        with patch('shutil.which', return_value=None):
            with pytest.raises(ExifToolNotFoundError):
                ExifToolWrapper()

    @patch('shutil.which', return_value='/usr/bin/exiftool')
    def test_get_metadata_success(self, mock_which):
        """Test successful metadata extraction."""
        mock_result = Mock()
        mock_result.stdout = json.dumps([{'File:FileName': 'test.jpg', 'EXIF:Make': 'Canon'}])
        
        with patch('subprocess.run', return_value=mock_result):
            with patch('pathlib.Path.exists', return_value=True):
                wrapper = ExifToolWrapper()
                metadata = wrapper.get_metadata('test.jpg')
                
                assert metadata == {'File:FileName': 'test.jpg', 'EXIF:Make': 'Canon'}

    @patch('shutil.which', return_value='/usr/bin/exiftool')
    def test_get_metadata_file_not_found(self, mock_which):
        """Test metadata extraction with non-existent file."""
        wrapper = ExifToolWrapper()
        
        with pytest.raises(FileNotFoundError):
            wrapper.get_metadata('nonexistent.jpg')

    @patch('shutil.which', return_value='/usr/bin/exiftool')
    def test_get_metadata_exiftool_error(self, mock_which):
        """Test metadata extraction with exiftool error."""
        with patch('subprocess.run', side_effect=subprocess.CalledProcessError(1, 'exiftool', stderr='Error')):
            wrapper = ExifToolWrapper()
            
            with patch('pathlib.Path.exists', return_value=True):
                with pytest.raises(ExifToolError):
                    wrapper.get_metadata('test.jpg')

    @patch('shutil.which', return_value='/usr/bin/exiftool')
    def test_get_metadata_json_decode_error(self, mock_which):
        """Test metadata extraction with invalid JSON."""
        mock_result = Mock()
        mock_result.stdout = 'invalid json'
        
        with patch('subprocess.run', return_value=mock_result):
            wrapper = ExifToolWrapper()
            
            with patch('pathlib.Path.exists', return_value=True):
                with pytest.raises(ExifToolError):
                    wrapper.get_metadata('test.jpg')

    @patch('shutil.which', return_value='/usr/bin/exiftool')
    def test_set_metadata_success(self, mock_which):
        """Test successful metadata setting."""
        mock_result = Mock()
        
        with patch('subprocess.run', return_value=mock_result):
            wrapper = ExifToolWrapper()
            
            with patch('pathlib.Path.exists', return_value=True):
                result = wrapper.set_metadata('test.jpg', {'EXIF:Make': 'Canon'})
                assert result is True

    @patch('shutil.which', return_value='/usr/bin/exiftool')
    def test_remove_metadata_all(self, mock_which):
        """Test removing all metadata."""
        mock_result = Mock()
        
        with patch('subprocess.run', return_value=mock_result):
            wrapper = ExifToolWrapper()
            
            with patch('pathlib.Path.exists', return_value=True):
                result = wrapper.remove_metadata('test.jpg')
                assert result is True

    @patch('shutil.which', return_value='/usr/bin/exiftool')
    def test_remove_metadata_specific_tags(self, mock_which):
        """Test removing specific metadata tags."""
        mock_result = Mock()
        
        with patch('subprocess.run', return_value=mock_result):
            wrapper = ExifToolWrapper()
            
            with patch('pathlib.Path.exists', return_value=True):
                result = wrapper.remove_metadata('test.jpg', ['EXIF:Make', 'EXIF:Model'])
                assert result is True

    @patch('shutil.which', return_value='/usr/bin/exiftool')
    def test_copy_metadata_success(self, mock_which):
        """Test successful metadata copying."""
        mock_result = Mock()
        
        with patch('subprocess.run', return_value=mock_result):
            wrapper = ExifToolWrapper()
            
            with patch('pathlib.Path.exists', return_value=True):
                result = wrapper.copy_metadata('source.jpg', 'target.jpg')
                assert result is True

    @patch('shutil.which', return_value='/usr/bin/exiftool')
    def test_backup_metadata_to_xml_string(self, mock_which):
        """Test backup metadata to XML string."""
        mock_xml = '<?xml version="1.0"?><rdf:RDF><rdf:Description><pdf:Title>Test</pdf:Title></rdf:Description></rdf:RDF>'
        mock_result = Mock()
        mock_result.stdout = mock_xml
        
        with patch('subprocess.run', return_value=mock_result):
            wrapper = ExifToolWrapper()
            
            with patch('pathlib.Path.exists', return_value=True):
                result = wrapper.backup_metadata_to_xml_string('test.pdf')
                assert result == mock_xml

    @patch('shutil.which', return_value='/usr/bin/exiftool')
    def test_backup_metadata_file_not_found(self, mock_which):
        """Test backup metadata with non-existent file."""
        wrapper = ExifToolWrapper()
        
        with pytest.raises(FileNotFoundError):
            wrapper.backup_metadata_to_xml_string('nonexistent.pdf')

    @patch('shutil.which', return_value='/usr/bin/exiftool')
    def test_restore_metadata_from_xml_string(self, mock_which):
        """Test restore metadata from XML string."""
        mock_result = Mock()
        xml_content = '<?xml version="1.0"?><rdf:RDF><rdf:Description><pdf:Title>Test</pdf:Title></rdf:Description></rdf:RDF>'
        
        with patch('subprocess.run', return_value=mock_result):
            wrapper = ExifToolWrapper()
            
            with patch('pathlib.Path.exists', return_value=True):
                with patch('tempfile.NamedTemporaryFile') as mock_temp:
                    mock_temp.return_value.__enter__.return_value.name = '/tmp/test.xml'
                    with patch('pathlib.Path.unlink'):
                        result = wrapper.restore_metadata_from_xml_string(xml_content, 'test.pdf')
                        assert result is True

    @patch('shutil.which', return_value='/usr/bin/exiftool')
    def test_restore_metadata_file_not_found(self, mock_which):
        """Test restore metadata with non-existent target file."""
        wrapper = ExifToolWrapper()
        xml_content = '<xml>test</xml>'
        
        with pytest.raises(FileNotFoundError):
            wrapper.restore_metadata_from_xml_string(xml_content, 'nonexistent.pdf')

    @patch('shutil.which', return_value='/usr/bin/exiftool')
    def test_restore_metadata_exiftool_error(self, mock_which):
        """Test restore metadata with exiftool error."""
        xml_content = '<xml>test</xml>'
        
        with patch('subprocess.run', side_effect=subprocess.CalledProcessError(1, 'exiftool', stderr='Error')):
            wrapper = ExifToolWrapper()
            
            with patch('pathlib.Path.exists', return_value=True):
                with patch('tempfile.NamedTemporaryFile') as mock_temp:
                    mock_temp.return_value.__enter__.return_value.name = '/tmp/test.xml'
                    with patch('pathlib.Path.unlink'):
                        result = wrapper.restore_metadata_from_xml_string(xml_content, 'test.pdf')
                        assert result is False


class TestMetadataProcessor:
    """Test MetadataProcessor functionality."""

    @patch('svk_xmp.core.metadata_processor.ExifToolWrapper')
    def test_init(self, mock_exiftool):
        """Test MetadataProcessor initialization."""
        processor = MetadataProcessor()
        mock_exiftool.assert_called_once_with(None)

    @patch('svk_xmp.core.metadata_processor.ExifToolWrapper')
    def test_init_with_custom_path(self, mock_exiftool):
        """Test MetadataProcessor initialization with custom path."""
        processor = MetadataProcessor('/custom/path')
        mock_exiftool.assert_called_once_with('/custom/path')

    @patch('svk_xmp.core.metadata_processor.ExifToolWrapper')
    def test_extract_basic_info(self, mock_exiftool):
        """Test basic info extraction."""
        mock_instance = mock_exiftool.return_value
        mock_instance.get_metadata.return_value = {
            'File:FileSize': '1024 bytes',
            'File:ImageWidth': 800,
            'File:ImageHeight': 600,
            'EXIF:Make': 'Canon',
            'EXIF:Model': 'EOS 5D',
            'EXIF:DateTimeOriginal': '2023:01:01 12:00:00',
            'EXIF:GPSLatitude': '59.3293',
            'EXIF:GPSLongitude': '18.0686'
        }
        
        processor = MetadataProcessor()
        result = processor.extract_basic_info('test.jpg')
        
        expected = {
            'filename': 'test.jpg',
            'file_size': '1024 bytes',
            'image_width': 800,
            'image_height': 600,
            'camera_make': 'Canon',
            'camera_model': 'EOS 5D',
            'date_taken': '2023:01:01 12:00:00',
            'gps_latitude': '59.3293',
            'gps_longitude': '18.0686'
        }
        
        assert result == expected

    @patch('svk_xmp.core.metadata_processor.ExifToolWrapper')
    def test_extract_basic_info_with_fallbacks(self, mock_exiftool):
        """Test basic info extraction with fallback fields."""
        mock_instance = mock_exiftool.return_value
        mock_instance.get_metadata.return_value = {
            'EXIF:ImageWidth': 800,
            'EXIF:ImageHeight': 600,
            'EXIF:DateTime': '2023:01:01 12:00:00'
        }
        
        processor = MetadataProcessor()
        result = processor.extract_basic_info('test.jpg')
        
        expected = {
            'filename': 'test.jpg',
            'file_size': 'Unknown',  # This gets added when no File:FileSize
            'image_width': 800,
            'image_height': 600,
            'date_taken': '2023:01:01 12:00:00'
        }
        
        assert result == expected

    @patch('svk_xmp.core.metadata_processor.ExifToolWrapper')
    def test_batch_process_extract(self, mock_exiftool):
        """Test batch processing with extract operation."""
        mock_instance = mock_exiftool.return_value
        mock_instance.get_metadata.return_value = {'EXIF:Make': 'Canon'}
        
        processor = MetadataProcessor()
        
        with patch.object(processor, 'extract_basic_info', return_value={'filename': 'test.jpg'}):
            results = processor.batch_process(['test1.jpg', 'test2.jpg'], 'extract')
            
            assert len(results) == 2
            assert all(result == {'filename': 'test.jpg'} for result in results)

    @patch('svk_xmp.core.metadata_processor.ExifToolWrapper')
    def test_batch_process_remove(self, mock_exiftool):
        """Test batch processing with remove operation."""
        mock_instance = mock_exiftool.return_value
        mock_instance.remove_metadata.return_value = True
        
        processor = MetadataProcessor()
        results = processor.batch_process(['test1.jpg', 'test2.jpg'], 'remove', tags=['EXIF:Make'])
        
        expected = [
            {'file': 'test1.jpg', 'success': True},
            {'file': 'test2.jpg', 'success': True}
        ]
        
        assert results == expected

    @patch('svk_xmp.core.metadata_processor.ExifToolWrapper')
    def test_batch_process_unknown_operation(self, mock_exiftool):
        """Test batch processing with unknown operation."""
        processor = MetadataProcessor()
        results = processor.batch_process(['test.jpg'], 'unknown')
        
        assert len(results) == 1
        assert 'error' in results[0]
        assert 'Unknown operation' in results[0]['error']

    @patch('svk_xmp.core.metadata_processor.ExifToolWrapper')
    def test_find_files_without_metadata(self, mock_exiftool):
        """Test finding files without metadata."""
        mock_instance = mock_exiftool.return_value
        
        def mock_get_metadata(path):
            if 'with_metadata' in str(path):
                return {'EXIF:Make': 'Canon', 'File:FileSize': '1024', 'EXIF:Model': 'EOS 5D'}
            else:
                return {'File:FileSize': '1024'}
        
        mock_instance.get_metadata.side_effect = mock_get_metadata
        
        processor = MetadataProcessor()
        
        with patch('pathlib.Path.rglob') as mock_rglob:
            # Mock rglob to return different files for different extensions
            def mock_rglob_side_effect(pattern):
                if pattern == '*.jpg':
                    return [Path('/test/with_metadata.jpg'), Path('/test/without_metadata.jpg')]
                else:
                    return []
            
            mock_rglob.side_effect = mock_rglob_side_effect
            
            results = processor.find_files_without_metadata('/test', ['.jpg'])
            
            assert len(results) == 1
            assert results[0] == Path('/test/without_metadata.jpg')

    @patch('svk_xmp.core.metadata_processor.ExifToolWrapper')
    def test_find_files_without_metadata_custom_extensions(self, mock_exiftool):
        """Test finding files without metadata with custom extensions."""
        mock_instance = mock_exiftool.return_value
        mock_instance.get_metadata.return_value = {'File:FileSize': '1024'}
        
        processor = MetadataProcessor()
        
        with patch('pathlib.Path.rglob') as mock_rglob:
            mock_rglob.return_value = [Path('/test/image.png')]
            
            results = processor.find_files_without_metadata('/test', ['.png'])
            
            assert len(results) == 1
            mock_rglob.assert_called_once_with('*.png')

    @patch('svk_xmp.core.metadata_processor.ExifToolWrapper')
    def test_backup_pdf_metadata(self, mock_exiftool):
        """Test PDF metadata backup to XML string."""
        mock_instance = mock_exiftool.return_value
        mock_xml_content = '<?xml version="1.0"?><rdf:RDF><rdf:Description><pdf:Title>Test PDF</pdf:Title></rdf:Description></rdf:RDF>'
        mock_instance.backup_metadata_to_xml_string.return_value = mock_xml_content
        
        processor = MetadataProcessor()
        result = processor.backup_pdf_metadata('test.pdf')
        
        assert result == mock_xml_content
        mock_instance.backup_metadata_to_xml_string.assert_called_once_with('test.pdf')

    @patch('svk_xmp.core.metadata_processor.ExifToolWrapper')
    def test_restore_pdf_metadata(self, mock_exiftool):
        """Test PDF metadata restore from XML string."""
        mock_instance = mock_exiftool.return_value
        mock_instance.restore_metadata_from_xml_string.return_value = True
        
        xml_content = '<?xml version="1.0"?><rdf:RDF><rdf:Description><pdf:Title>Test PDF</pdf:Title></rdf:Description></rdf:RDF>'
        
        processor = MetadataProcessor()
        result = processor.restore_pdf_metadata(xml_content, 'test.pdf')
        
        assert result is True
        mock_instance.restore_metadata_from_xml_string.assert_called_once_with(xml_content, 'test.pdf')

    @patch('svk_xmp.core.metadata_processor.ExifToolWrapper')
    def test_pdf_backup_remove_restore_workflow(self, mock_exiftool):
        """Test complete backup-remove-restore workflow for PDF files."""
        mock_instance = mock_exiftool.return_value
        
        # Mock XML backup content
        mock_xml_backup = '<?xml version="1.0"?><rdf:RDF><rdf:Description><pdf:Title>Original Title</pdf:Title><pdf:Author>Test Author</pdf:Author></rdf:Description></rdf:RDF>'
        mock_instance.backup_metadata_to_xml_string.return_value = mock_xml_backup
        mock_instance.remove_metadata.return_value = True
        mock_instance.restore_metadata_from_xml_string.return_value = True
        
        processor = MetadataProcessor()
        
        # 1. Backup metadata
        xml_backup = processor.backup_pdf_metadata('test.pdf')
        assert xml_backup == mock_xml_backup
        mock_instance.backup_metadata_to_xml_string.assert_called_once_with('test.pdf')
        
        # 2. Remove metadata (simulating ghostscript conversion)
        remove_success = mock_instance.remove_metadata('test.pdf')
        assert remove_success is True
        
        # 3. Restore metadata from backup
        restore_success = processor.restore_pdf_metadata(xml_backup, 'test.pdf')
        assert restore_success is True
        mock_instance.restore_metadata_from_xml_string.assert_called_once_with(xml_backup, 'test.pdf')

    @patch('svk_xmp.core.metadata_processor.ExifToolWrapper')
    def test_pdf_backup_remove_restore_workflow_with_failure(self, mock_exiftool):
        """Test backup-remove-restore workflow when restore fails."""
        mock_instance = mock_exiftool.return_value
        
        mock_xml_backup = '<xml>backup</xml>'
        mock_instance.backup_metadata_to_xml_string.return_value = mock_xml_backup
        mock_instance.remove_metadata.return_value = True
        mock_instance.restore_metadata_from_xml_string.return_value = False  # Simulate failure
        
        processor = MetadataProcessor()
        
        # Backup and remove succeed
        xml_backup = processor.backup_pdf_metadata('test.pdf')
        assert xml_backup == mock_xml_backup
        
        remove_success = mock_instance.remove_metadata('test.pdf')
        assert remove_success is True
        
        # Restore fails
        restore_success = processor.restore_pdf_metadata(xml_backup, 'test.pdf')
        assert restore_success is False