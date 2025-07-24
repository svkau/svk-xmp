"""Tests for core functionality."""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import json
import subprocess
import zipfile

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

    @patch('shutil.which', return_value='/usr/bin/exiftool')
    def test_sync_metadata_single_file_success(self, mock_which):
        """Test successful sync of single file."""
        wrapper = ExifToolWrapper()
        
        # Mock validation
        mock_validate_result = Mock()
        mock_validate_result.stderr = ""
        
        # Mock sync operation  
        mock_sync_result = Mock()
        mock_sync_result.stderr = ""
        
        with patch('subprocess.run', side_effect=[mock_validate_result, mock_sync_result]):
            with patch('pathlib.Path.exists', return_value=True):
                with patch.object(wrapper, '_get_files_to_process', return_value=[Path('test.jpg')]):
                    result = wrapper.sync_metadata('test.jpg', verbose=True)
                    
                    assert result['summary']['total_files'] == 1
                    assert result['summary']['processed'] == 1
                    assert result['summary']['errors'] == 0
                    assert result['processed'] == ['test.jpg']

    @patch('shutil.which', return_value='/usr/bin/exiftool')
    def test_sync_metadata_directory_success(self, mock_which):
        """Test successful sync of directory."""
        wrapper = ExifToolWrapper()
        
        # Mock validation and sync for multiple files
        mock_validate_result = Mock()
        mock_validate_result.stderr = ""
        
        mock_sync_result = Mock()
        mock_sync_result.stderr = ""
        
        test_files = [Path('dir/test1.jpg'), Path('dir/test2.jpg')]
        
        with patch('subprocess.run', side_effect=[mock_validate_result, mock_sync_result] * 2):
            with patch('pathlib.Path.exists', return_value=True):
                with patch.object(wrapper, '_get_files_to_process', return_value=test_files):
                    result = wrapper.sync_metadata('test_dir', verbose=False)
                    
                    assert result['summary']['total_files'] == 2
                    assert result['summary']['processed'] == 2
                    assert result['summary']['errors'] == 0
                    assert len(result['processed']) == 2

    @patch('shutil.which', return_value='/usr/bin/exiftool')
    def test_sync_metadata_with_validation_error(self, mock_which):
        """Test sync with validation error."""
        wrapper = ExifToolWrapper()
        
        # Mock validation failure
        mock_validate_result = Mock()
        mock_validate_result.stderr = "Error: Invalid JPEG format"
        
        with patch('subprocess.run', return_value=mock_validate_result):
            with patch('pathlib.Path.exists', return_value=True):
                with patch.object(wrapper, '_get_files_to_process', return_value=[Path('bad.jpg')]):
                    result = wrapper.sync_metadata('bad.jpg', verbose=True)
                    
                    assert result['summary']['total_files'] == 1
                    assert result['summary']['processed'] == 0
                    assert result['summary']['errors'] == 1
                    assert len(result['errors']) == 1
                    assert 'bad.jpg' in result['errors'][0]['file']

    @patch('shutil.which', return_value='/usr/bin/exiftool')
    def test_sync_metadata_with_warnings(self, mock_which):
        """Test sync with warnings."""
        wrapper = ExifToolWrapper()
        
        # Mock validation
        mock_validate_result = Mock()
        mock_validate_result.stderr = ""
        
        # Mock sync with warnings
        mock_sync_result = Mock()
        mock_sync_result.stderr = "Warning: Missing GPS data\nWarning: No IPTC data found"
        
        with patch('subprocess.run', side_effect=[mock_validate_result, mock_sync_result]):
            with patch('pathlib.Path.exists', return_value=True):
                with patch.object(wrapper, '_get_files_to_process', return_value=[Path('test.jpg')]):
                    result = wrapper.sync_metadata('test.jpg', verbose=True)
                    
                    assert result['summary']['total_files'] == 1
                    assert result['summary']['processed'] == 1
                    assert result['summary']['warnings'] == 2
                    assert len(result['warnings']) == 2
                    assert 'Missing GPS data' in result['warnings'][0]['warning']

    @patch('shutil.which', return_value='/usr/bin/exiftool')
    def test_sync_metadata_file_not_found(self, mock_which):
        """Test sync with nonexistent file."""
        wrapper = ExifToolWrapper()
        
        with pytest.raises(FileNotFoundError):
            wrapper.sync_metadata('nonexistent.jpg')

    @patch('shutil.which', return_value='/usr/bin/exiftool')
    def test_sync_metadata_args_file_not_found(self, mock_which):
        """Test sync with nonexistent args file."""
        wrapper = ExifToolWrapper()
        
        with patch('pathlib.Path.exists', return_value=False):
            with pytest.raises(FileNotFoundError, match="Arguments file not found"):
                wrapper.sync_metadata('test.jpg', args_file='nonexistent.args')

    @patch('shutil.which', return_value='/usr/bin/exiftool')
    def test_sync_metadata_skip_unsupported_files(self, mock_which):
        """Test sync skipping unsupported file types."""
        wrapper = ExifToolWrapper()
        
        with patch('pathlib.Path.exists', return_value=True):
            with patch.object(wrapper, '_get_files_to_process', return_value=[Path('test.txt')]):
                result = wrapper.sync_metadata('test.txt', verbose=True)
                
                assert result['summary']['total_files'] == 1
                assert result['summary']['processed'] == 0
                assert result['summary']['skipped'] == 1
                assert result['skipped'] == ['test.txt']

    @patch('shutil.which', return_value='/usr/bin/exiftool')
    def test_get_files_to_process_single_file(self, mock_which):
        """Test file discovery for single file."""
        wrapper = ExifToolWrapper()
        
        with patch('pathlib.Path.exists', return_value=True):
            with patch('pathlib.Path.is_file', return_value=True):
                with patch('pathlib.Path.suffix', new_property=lambda x: '.jpg'):
                    files = wrapper._get_files_to_process(Path('test.jpg'), ['.jpg'], True)
                    assert files == [Path('test.jpg')]

    # Note: Directory file discovery is tested through integration tests
    # The _get_files_to_process method is complex to mock due to Path method interactions


    @patch('shutil.which', return_value='/usr/bin/exiftool')
    def test_sync_metadata_skip_zip_files(self, mock_which):
        """Test that zip files are properly skipped with explanation."""
        wrapper = ExifToolWrapper()
        
        with patch('pathlib.Path.exists', return_value=True):
            with patch.object(wrapper, '_get_files_to_process', return_value=[Path('test.zip')]):
                result = wrapper.sync_metadata('test.zip', verbose=True)
                
                assert result['summary']['total_files'] == 1
                assert result['summary']['processed'] == 0
                assert result['summary']['skipped'] == 1
                assert result['skipped'] == ['test.zip']

    @patch('shutil.which', return_value='/usr/bin/exiftool')
    def test_validate_file_success(self, mock_which):
        """Test successful file validation."""
        wrapper = ExifToolWrapper()
        
        mock_result = Mock()
        mock_result.stderr = ""
        
        with patch('subprocess.run', return_value=mock_result):
            # Should not raise exception
            wrapper._validate_file('test.jpg')

    @patch('shutil.which', return_value='/usr/bin/exiftool')
    def test_validate_file_with_warnings(self, mock_which):
        """Test file validation with warnings."""
        wrapper = ExifToolWrapper()
        
        mock_result = Mock()
        mock_result.stderr = "Warning: Minor corruption detected"
        
        with patch('subprocess.run', return_value=mock_result):
            # Should not raise exception for warnings
            wrapper._validate_file('test.jpg')

    @patch('shutil.which', return_value='/usr/bin/exiftool')
    def test_validate_file_with_error(self, mock_which):
        """Test file validation with errors."""
        wrapper = ExifToolWrapper()
        
        mock_result = Mock()
        mock_result.stderr = "Error: File is corrupted"
        
        with patch('subprocess.run', return_value=mock_result):
            with pytest.raises(ExifToolError):
                wrapper._validate_file('test.jpg')

    @patch('shutil.which', return_value='/usr/bin/exiftool')
    def test_validate_file_command_failure(self, mock_which):
        """Test file validation when command fails."""
        wrapper = ExifToolWrapper()
        
        with patch('subprocess.run', side_effect=subprocess.CalledProcessError(1, 'exiftool', stderr='Command failed')):
            with pytest.raises(ExifToolError):
                wrapper._validate_file('test.jpg')


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

    @patch('svk_xmp.core.metadata_processor.ExifToolWrapper')
    def test_sync_metadata_success(self, mock_exiftool):
        """Test successful metadata synchronization."""
        mock_instance = mock_exiftool.return_value
        mock_sync_result = {
            'processed': ['test.jpg'],
            'errors': [],
            'warnings': [],
            'skipped': [],
            'summary': {
                'total_files': 1,
                'processed': 1,
                'errors': 0,
                'warnings': 0,
                'skipped': 0
            }
        }
        mock_instance.sync_metadata.return_value = mock_sync_result
        
        processor = MetadataProcessor()
        result = processor.sync_metadata('test.jpg')
        
        assert result == mock_sync_result
        mock_instance.sync_metadata.assert_called_once_with(
            path='test.jpg',
            args_file='arg_files/metadata_sync_images.args',
            file_extensions=None,
            recursive=True,
            verbose=False,
            progress_callback=None
        )

    @patch('svk_xmp.core.metadata_processor.ExifToolWrapper')
    def test_sync_metadata_with_custom_args(self, mock_exiftool):
        """Test metadata synchronization with custom arguments."""
        mock_instance = mock_exiftool.return_value
        mock_sync_result = {
            'processed': [],
            'errors': [],
            'warnings': [],
            'skipped': [],
            'summary': {'total_files': 0, 'processed': 0, 'errors': 0, 'warnings': 0, 'skipped': 0}
        }
        mock_instance.sync_metadata.return_value = mock_sync_result
        
        processor = MetadataProcessor()
        
        def progress_callback(file, index, total):
            pass
        
        result = processor.sync_metadata(
            path='/test/dir',
            args_file='custom.args',
            file_extensions=['.jpg', '.png'],
            recursive=False,
            verbose=True,
            progress_callback=progress_callback
        )
        
        assert result == mock_sync_result
        mock_instance.sync_metadata.assert_called_once_with(
            path='/test/dir',
            args_file='custom.args',
            file_extensions=['.jpg', '.png'],
            recursive=False,
            verbose=True,
            progress_callback=progress_callback
        )

    @patch('svk_xmp.core.metadata_processor.ExifToolWrapper')
    def test_sync_metadata_error_handling(self, mock_exiftool):
        """Test metadata sync error handling and exception wrapping."""
        mock_instance = mock_exiftool.return_value
        mock_instance.sync_metadata.side_effect = Exception("Exiftool failed")
        
        processor = MetadataProcessor()
        
        with pytest.raises(MetadataProcessingError) as exc_info:
            processor.sync_metadata('test.jpg')
        
        assert "Failed to sync metadata: Exiftool failed" in str(exc_info.value)

    @patch('svk_xmp.core.metadata_processor.ExifToolWrapper')
    def test_sync_metadata_with_file_not_found_error(self, mock_exiftool):
        """Test metadata sync when file is not found."""
        mock_instance = mock_exiftool.return_value
        mock_instance.sync_metadata.side_effect = FileNotFoundError("Path not found: test.jpg")
        
        processor = MetadataProcessor()
        
        with pytest.raises(MetadataProcessingError) as exc_info:
            processor.sync_metadata('test.jpg')
        
        assert "Failed to sync metadata: Path not found: test.jpg" in str(exc_info.value)

    @patch('svk_xmp.core.metadata_processor.ExifToolWrapper')
    def test_sync_metadata_with_exiftool_error(self, mock_exiftool):
        """Test metadata sync when exiftool command fails."""
        mock_instance = mock_exiftool.return_value
        mock_instance.sync_metadata.side_effect = ExifToolError("exiftool command failed")
        
        processor = MetadataProcessor()
        
        with pytest.raises(MetadataProcessingError) as exc_info:
            processor.sync_metadata('test.jpg')
        
        assert "Failed to sync metadata: exiftool command failed" in str(exc_info.value)

    @patch('shutil.which', return_value='/usr/bin/exiftool')
    def test_extract_xmp_packet_success(self, mock_which):
        """Test successful XMP packet extraction."""
        wrapper = ExifToolWrapper()
        
        mock_xmp_content = '<?xpacket begin="\ufeff" id="W5M0MpCehiHzreSzNTczkc9d"?>\n<x:xmpmeta xmlns:x="adobe:ns:meta/" x:xmptk="Image::ExifTool 12.76">\n<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">\n<rdf:Description rdf:about=""\n  xmlns:dc="http://purl.org/dc/elements/1.1/">\n  <dc:title>\n   <rdf:Alt>\n    <rdf:li xml:lang="x-default">Test Title</rdf:li>\n   </rdf:Alt>\n  </dc:title>\n</rdf:Description>\n</rdf:RDF>\n</x:xmpmeta>\n<?xpacket end="w"?>'
        
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = mock_xmp_content
        mock_result.stderr = ""
        
        with patch('subprocess.run', return_value=mock_result):
            with patch('pathlib.Path.exists', return_value=True):
                result = wrapper.extract_xmp_packet('test.jpg')
                assert result == mock_xmp_content

    @patch('shutil.which', return_value='/usr/bin/exiftool')
    def test_extract_xmp_packet_no_xmp(self, mock_which):
        """Test XMP packet extraction when no XMP exists."""
        wrapper = ExifToolWrapper()
        
        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "No XMP data found"
        
        with patch('subprocess.run', return_value=mock_result):
            with patch('pathlib.Path.exists', return_value=True):
                result = wrapper.extract_xmp_packet('test.jpg')
                assert result == ""

    @patch('shutil.which', return_value='/usr/bin/exiftool')
    def test_extract_xmp_packet_file_not_found(self, mock_which):
        """Test XMP packet extraction with non-existent file."""
        wrapper = ExifToolWrapper()
        
        with pytest.raises(FileNotFoundError):
            wrapper.extract_xmp_packet('nonexistent.jpg')

    @patch('shutil.which', return_value='/usr/bin/exiftool')
    def test_extract_xmp_xml_success(self, mock_which):
        """Test successful XMP XML extraction."""
        wrapper = ExifToolWrapper()
        
        mock_xmp_packet = '<?xpacket begin="\ufeff" id="W5M0MpCehiHzreSzNTczkc9d"?>\n<x:xmpmeta xmlns:x="adobe:ns:meta/" x:xmptk="Image::ExifTool 12.76">\n<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">\n<rdf:Description rdf:about=""\n  xmlns:dc="http://purl.org/dc/elements/1.1/">\n  <dc:title>\n   <rdf:Alt>\n    <rdf:li xml:lang="x-default">Test Title</rdf:li>\n   </rdf:Alt>\n  </dc:title>\n</rdf:Description>\n</rdf:RDF>\n</x:xmpmeta>\n<?xpacket end="w"?>'
        expected_xml = '<x:xmpmeta xmlns:x="adobe:ns:meta/" x:xmptk="Image::ExifTool 12.76">\n<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">\n<rdf:Description rdf:about=""\n  xmlns:dc="http://purl.org/dc/elements/1.1/">\n  <dc:title>\n   <rdf:Alt>\n    <rdf:li xml:lang="x-default">Test Title</rdf:li>\n   </rdf:Alt>\n  </dc:title>\n</rdf:Description>\n</rdf:RDF>\n</x:xmpmeta>'
        
        with patch.object(wrapper, 'extract_xmp_packet', return_value=mock_xmp_packet):
            result = wrapper.extract_xmp_xml('test.jpg')
            assert result == expected_xml

    @patch('shutil.which', return_value='/usr/bin/exiftool')
    def test_extract_xmp_xml_no_xmp(self, mock_which):
        """Test XMP XML extraction when no XMP exists."""
        wrapper = ExifToolWrapper()
        
        with patch.object(wrapper, 'extract_xmp_packet', return_value=""):
            result = wrapper.extract_xmp_xml('test.jpg')
            assert result == ""

    @patch('svk_xmp.core.metadata_processor.ExifToolWrapper')
    def test_processor_extract_xmp_xml_success(self, mock_exiftool):
        """Test MetadataProcessor XMP XML extraction."""
        mock_instance = mock_exiftool.return_value
        mock_xml = '<x:xmpmeta xmlns:x="adobe:ns:meta/"><rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"><rdf:Description xmlns:dc="http://purl.org/dc/elements/1.1/"><dc:title><rdf:Alt><rdf:li xml:lang="x-default">Test Title</rdf:li></rdf:Alt></dc:title></rdf:Description></rdf:RDF></x:xmpmeta>'
        mock_instance.extract_xmp_xml.return_value = mock_xml
        
        processor = MetadataProcessor()
        result = processor.extract_xmp_xml('test.jpg')
        
        assert result == mock_xml
        mock_instance.extract_xmp_xml.assert_called_once_with('test.jpg')

    @patch('svk_xmp.core.metadata_processor.ExifToolWrapper')
    def test_processor_extract_xmp_packet_success(self, mock_exiftool):
        """Test MetadataProcessor XMP packet extraction."""
        mock_instance = mock_exiftool.return_value
        mock_packet = '<?xpacket begin="\ufeff"?><x:xmpmeta>content</x:xmpmeta><?xpacket end="w"?>'
        mock_instance.extract_xmp_packet.return_value = mock_packet
        
        processor = MetadataProcessor()
        result = processor.extract_xmp_packet('test.jpg')
        
        assert result == mock_packet
        mock_instance.extract_xmp_packet.assert_called_once_with('test.jpg')

    @patch('svk_xmp.core.metadata_processor.ExifToolWrapper')
    def test_processor_extract_xmp_error_handling(self, mock_exiftool):
        """Test MetadataProcessor XMP extraction error handling."""
        mock_instance = mock_exiftool.return_value
        mock_instance.extract_xmp_xml.side_effect = Exception("Exiftool failed")
        
        processor = MetadataProcessor()
        
        with pytest.raises(MetadataProcessingError) as exc_info:
            processor.extract_xmp_xml('test.jpg')
        
        assert "Failed to extract XMP: Exiftool failed" in str(exc_info.value)

    def test_parse_xmp_fields_success(self):
        """Test XMP field parsing."""
        processor = MetadataProcessor()
        
        xmp_xml = '''<x:xmpmeta xmlns:x="adobe:ns:meta/" x:xmptk="Image::ExifTool 12.76">
        <rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
         <rdf:Description rdf:about=""
          xmlns:dc="http://purl.org/dc/elements/1.1/"
          xmlns:xmp="http://ns.adobe.com/xap/1.0/"
          xmlns:photoshop="http://ns.adobe.com/photoshop/1.0/">
          <dc:title>
           <rdf:Alt>
            <rdf:li xml:lang="x-default">Test Title</rdf:li>
           </rdf:Alt>
          </dc:title>
          <dc:description>
           <rdf:Alt>
            <rdf:li xml:lang="x-default">Test Description</rdf:li>
           </rdf:Alt>
          </dc:description>
          <xmp:CreateDate>2023-01-01T12:00:00Z</xmp:CreateDate>
          <dc:creator>
           <rdf:Seq>
            <rdf:li>Test Creator</rdf:li>
           </rdf:Seq>
          </dc:creator>
          <dc:subject>
           <rdf:Bag>
            <rdf:li>keyword1</rdf:li>
            <rdf:li>keyword2</rdf:li>
           </rdf:Bag>
          </dc:subject>
         </rdf:Description>
        </rdf:RDF>
        </x:xmpmeta>'''
        
        fields = processor.parse_xmp_fields(xmp_xml)
        
        expected = {
            'title': 'Test Title',
            'description': 'Test Description',
            'date_created': '2023-01-01T12:00:00Z',
            'creator': 'Test Creator',
            'keywords': 'keyword1, keyword2'
        }
        
        assert fields == expected

    def test_parse_xmp_fields_empty_xml(self):
        """Test XMP field parsing with empty XML."""
        processor = MetadataProcessor()
        
        fields = processor.parse_xmp_fields("")
        
        expected = {}
        assert fields == expected

    def test_parse_xmp_fields_invalid_xml(self):
        """Test XMP field parsing with invalid XML."""
        processor = MetadataProcessor()
        
        fields = processor.parse_xmp_fields("<invalid>xml</not_closed>")
        
        expected = {
            'title': '',
            'description': '',
            'date_created': '',
            'creator': '',
            'keywords': ''
        }
        assert fields == expected

    @patch('svk_xmp.core.metadata_processor.ExifToolWrapper')
    def test_batch_extract_xmp_success(self, mock_exiftool):
        """Test batch XMP extraction (non-persistent mode)."""
        mock_instance = mock_exiftool.return_value
        
        # Mock file discovery
        test_files = [Path('test1.jpg'), Path('test2.jpg')]
        mock_instance._get_files_to_process.return_value = test_files
        
        processor = MetadataProcessor()
        
        # Mock XMP extraction for each file
        def mock_extract_xmp_xml(file_path):
            if 'test1' in str(file_path):
                return '<x:xmpmeta><rdf:RDF><rdf:Description xmlns:dc="http://purl.org/dc/elements/1.1/"><dc:title><rdf:Alt><rdf:li>Title 1</rdf:li></rdf:Alt></dc:title></rdf:Description></rdf:RDF></x:xmpmeta>'
            else:
                return ''  # No XMP for test2.jpg
        
        with patch.object(processor, 'extract_xmp_xml', side_effect=mock_extract_xmp_xml):
            with patch.object(processor, 'parse_xmp_fields', return_value={'title': 'Title 1'}):
                # Use non-persistent mode to avoid persistent wrapper mocking complexity
                result = processor.batch_extract_xmp('/test/dir', use_persistent=False)
        
        assert result['summary']['total_files'] == 2
        assert result['summary']['processed'] == 1
        assert result['summary']['skipped'] == 1
        assert len(result['processed']) == 1
        assert len(result['skipped']) == 1

    @patch('svk_xmp.core.metadata_processor.ExifToolWrapper')
    def test_batch_extract_xmp_with_errors(self, mock_exiftool):
        """Test batch XMP extraction with errors (non-persistent mode)."""
        mock_instance = mock_exiftool.return_value
        
        test_files = [Path('test1.jpg'), Path('test2.jpg')]
        mock_instance._get_files_to_process.return_value = test_files
        
        processor = MetadataProcessor()
        
        # Mock XMP extraction with error for second file
        def mock_extract_xmp_xml(file_path):
            if 'test1' in str(file_path):
                return '<x:xmpmeta>content</x:xmpmeta>'
            else:
                raise Exception("Processing error")
        
        with patch.object(processor, 'extract_xmp_xml', side_effect=mock_extract_xmp_xml):
            with patch.object(processor, 'parse_xmp_fields', return_value={'title': 'Test'}):
                # Use non-persistent mode to avoid persistent wrapper mocking complexity
                result = processor.batch_extract_xmp('/test/dir', use_persistent=False)
        
        assert result['summary']['total_files'] == 2
        assert result['summary']['processed'] == 1
        assert result['summary']['errors'] == 1
        assert len(result['processed']) == 1
        assert len(result['errors']) == 1

    @patch('shutil.which', return_value='/usr/bin/exiftool')
    def test_persistent_mode_context_manager(self, mock_which):
        """Test persistent mode as context manager."""
        with patch('subprocess.Popen') as mock_popen:
            mock_process = Mock()
            mock_process.stdin = Mock()
            mock_process.stdout = Mock()
            mock_process.stderr = Mock()
            mock_popen.return_value = mock_process
            
            with ExifToolWrapper(persistent=True) as wrapper:
                assert wrapper.persistent is True
                assert wrapper._process is not None
                mock_popen.assert_called_once()
            
            # Verify process was terminated
            mock_process.stdin.write.assert_called()
            mock_process.stdin.flush.assert_called()

    @patch('shutil.which', return_value='/usr/bin/exiftool')
    def test_batch_get_metadata(self, mock_which):
        """Test batch metadata extraction."""
        wrapper = ExifToolWrapper()
        
        mock_result = Mock()
        mock_result.stdout = json.dumps([
            {'File:FileName': 'test1.jpg', 'EXIF:Make': 'Canon'},
            {'File:FileName': 'test2.jpg', 'EXIF:Make': 'Nikon'}
        ])
        
        with patch.object(wrapper, '_run_command', return_value=mock_result):
            with patch('pathlib.Path.exists', return_value=True):
                results = wrapper.batch_get_metadata(['test1.jpg', 'test2.jpg'])
                
                assert len(results) == 2
                assert results[0]['EXIF:Make'] == 'Canon'
                assert results[1]['EXIF:Make'] == 'Nikon'

    @patch('shutil.which', return_value='/usr/bin/exiftool')
    def test_batch_extract_xmp_xml(self, mock_which):
        """Test batch XMP XML extraction."""
        wrapper = ExifToolWrapper()
        
        def mock_extract_xmp_xml(file_path):
            if 'test1' in str(file_path):
                return '<x:xmpmeta>test1 content</x:xmpmeta>'
            else:
                return '<x:xmpmeta>test2 content</x:xmpmeta>'
        
        with patch.object(wrapper, 'extract_xmp_xml', side_effect=mock_extract_xmp_xml):
            results = wrapper.batch_extract_xmp_xml(['test1.jpg', 'test2.jpg'])
            
            assert len(results) == 2
            assert 'test1 content' in results['test1.jpg']
            assert 'test2 content' in results['test2.jpg']

    @patch('svk_xmp.core.metadata_processor.ExifToolWrapper')
    def test_processor_batch_extract_xmp_persistent_mode(self, mock_exiftool_class):
        """Test MetadataProcessor batch XMP extraction with persistent mode."""
        # Mock the regular wrapper
        mock_regular_wrapper = Mock()
        mock_regular_wrapper.exiftool_path = 'exiftool'
        mock_regular_wrapper._get_files_to_process.return_value = [Path('test1.jpg'), Path('test2.jpg')]
        mock_exiftool_class.return_value = mock_regular_wrapper
        
        # Mock the persistent wrapper
        mock_persistent_wrapper = Mock()
        mock_persistent_wrapper.batch_extract_xmp_xml.return_value = {
            'test1.jpg': '<x:xmpmeta>content1</x:xmpmeta>',
            'test2.jpg': '<x:xmpmeta>content2</x:xmpmeta>'
        }
        
        # Mock the context manager
        mock_exiftool_class.return_value.__enter__ = Mock(return_value=mock_persistent_wrapper)
        mock_exiftool_class.return_value.__exit__ = Mock(return_value=None)
        
        processor = MetadataProcessor()
        
        with patch.object(processor, 'parse_xmp_fields', return_value={'title': 'Test'}):
            result = processor.batch_extract_xmp('/test/dir', use_persistent=True)
        
        assert result['summary']['total_files'] == 2
        assert result['summary']['processed'] == 2
        assert len(result['processed']) == 2

    @patch('svk_xmp.core.metadata_processor.ExifToolWrapper')
    def test_processor_batch_extract_xmp_fallback_to_individual(self, mock_exiftool_class):
        """Test MetadataProcessor falls back to individual processing for single files."""
        mock_wrapper = Mock()
        mock_wrapper.exiftool_path = 'exiftool'
        mock_wrapper._get_files_to_process.return_value = [Path('single.jpg')]
        mock_exiftool_class.return_value = mock_wrapper
        
        processor = MetadataProcessor()
        
        with patch.object(processor, 'extract_xmp_xml', return_value='<x:xmpmeta>content</x:xmpmeta>'):
            with patch.object(processor, 'parse_xmp_fields', return_value={'title': 'Test'}):
                result = processor.batch_extract_xmp('/test/dir', use_persistent=True)
        
        # Should use individual processing for single file
        assert result['summary']['total_files'] == 1
        assert result['summary']['processed'] == 1