"""Tests for CLI functionality."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from click.testing import CliRunner
import json

from svk_xmp.cli.commands import main, extract, remove, scan
from svk_xmp.core.exceptions import MyProjectError


class TestCLICommands:
    """Test CLI command functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    def test_main_group_help(self):
        """Test main command group help."""
        result = self.runner.invoke(main, ['--help'])
        assert result.exit_code == 0
        assert 'Metadata processing tool using exiftool' in result.output

    def test_main_with_exiftool_path(self):
        """Test main command with custom exiftool path."""
        with patch('svk_xmp.cli.commands.MetadataProcessor') as mock_processor:
            mock_instance = mock_processor.return_value
            mock_instance.extract_basic_info.return_value = {'filename': 'test.jpg'}
            
            with self.runner.isolated_filesystem():
                # Create a test file
                with open('test.jpg', 'w') as f:
                    f.write('test')
                
                result = self.runner.invoke(main, ['--exiftool-path', '/custom/path', 'extract', 'test.jpg'])
                # The path should be passed to the processor
                mock_processor.assert_called_with('/custom/path')

    @patch('svk_xmp.cli.commands.MetadataProcessor')
    def test_extract_command_table_format(self, mock_processor):
        """Test extract command with table format output."""
        mock_instance = mock_processor.return_value
        mock_instance.extract_basic_info.return_value = {
            'filename': 'test.jpg',
            'camera_make': 'Canon',
            'camera_model': 'EOS 5D'
        }
        
        with self.runner.isolated_filesystem():
            # Create a test file
            with open('test.jpg', 'w') as f:
                f.write('test')
            
            result = self.runner.invoke(main, ['extract', 'test.jpg'])
            
            assert result.exit_code == 0
            assert 'filename: test.jpg' in result.output
            assert 'camera_make: Canon' in result.output
            assert 'camera_model: EOS 5D' in result.output

    @patch('svk_xmp.cli.commands.MetadataProcessor')
    def test_extract_command_json_format(self, mock_processor):
        """Test extract command with JSON format output."""
        mock_instance = mock_processor.return_value
        mock_instance.extract_basic_info.return_value = {
            'filename': 'test.jpg',
            'camera_make': 'Canon'
        }
        
        with self.runner.isolated_filesystem():
            # Create a test file
            with open('test.jpg', 'w') as f:
                f.write('test')
            
            result = self.runner.invoke(main, ['extract', 'test.jpg', '--format', 'json'])
            
            assert result.exit_code == 0
            output_data = json.loads(result.output)
            assert output_data['filename'] == 'test.jpg'
            assert output_data['camera_make'] == 'Canon'

    @patch('svk_xmp.cli.commands.MetadataProcessor')
    def test_extract_command_error(self, mock_processor):
        """Test extract command with error handling."""
        mock_instance = mock_processor.return_value
        mock_instance.extract_basic_info.side_effect = MyProjectError("Test error")
        
        with self.runner.isolated_filesystem():
            # Create a test file
            with open('test.jpg', 'w') as f:
                f.write('test')
            
            result = self.runner.invoke(main, ['extract', 'test.jpg'])
            
            assert result.exit_code == 1
            assert 'Error: Test error' in result.output

    def test_extract_command_nonexistent_file(self):
        """Test extract command with nonexistent file."""
        result = self.runner.invoke(main, ['extract', 'nonexistent.jpg'])
        assert result.exit_code == 2  # Click's exit code for invalid arguments

    @patch('svk_xmp.cli.commands.MetadataProcessor')
    def test_remove_command_all_metadata(self, mock_processor):
        """Test remove command with --all flag."""
        mock_instance = mock_processor.return_value
        mock_instance.exiftool.remove_metadata.return_value = True
        
        with self.runner.isolated_filesystem():
            # Create a test file
            with open('test.jpg', 'w') as f:
                f.write('test')
            
            result = self.runner.invoke(main, ['remove', 'test.jpg', '--all'])
            
            assert result.exit_code == 0
            assert 'Metadata removed from test.jpg' in result.output
            mock_instance.exiftool.remove_metadata.assert_called_once_with('test.jpg')

    @patch('svk_xmp.cli.commands.MetadataProcessor')
    def test_remove_command_specific_tags(self, mock_processor):
        """Test remove command with specific tags."""
        mock_instance = mock_processor.return_value
        mock_instance.exiftool.remove_metadata.return_value = True
        
        with self.runner.isolated_filesystem():
            # Create a test file
            with open('test.jpg', 'w') as f:
                f.write('test')
            
            result = self.runner.invoke(main, ['remove', 'test.jpg', '--tags', 'EXIF:Make', '--tags', 'EXIF:Model'])
            
            assert result.exit_code == 0
            assert 'Metadata removed from test.jpg' in result.output
            mock_instance.exiftool.remove_metadata.assert_called_once_with('test.jpg', ['EXIF:Make', 'EXIF:Model'])

    @patch('svk_xmp.cli.commands.MetadataProcessor')
    def test_remove_command_failure(self, mock_processor):
        """Test remove command with removal failure."""
        mock_instance = mock_processor.return_value
        mock_instance.exiftool.remove_metadata.return_value = False
        
        with self.runner.isolated_filesystem():
            # Create a test file
            with open('test.jpg', 'w') as f:
                f.write('test')
            
            result = self.runner.invoke(main, ['remove', 'test.jpg', '--all'])
            
            assert result.exit_code == 0
            assert 'Failed to remove metadata from test.jpg' in result.output

    @patch('svk_xmp.cli.commands.MetadataProcessor')
    def test_remove_command_error(self, mock_processor):
        """Test remove command with error handling."""
        mock_instance = mock_processor.return_value
        mock_instance.exiftool.remove_metadata.side_effect = MyProjectError("Test error")
        
        with self.runner.isolated_filesystem():
            # Create a test file
            with open('test.jpg', 'w') as f:
                f.write('test')
            
            result = self.runner.invoke(main, ['remove', 'test.jpg', '--all'])
            
            assert result.exit_code == 1
            assert 'Error: Test error' in result.output

    @patch('svk_xmp.cli.commands.MetadataProcessor')
    def test_scan_command_files_found(self, mock_processor):
        """Test scan command when files without metadata are found."""
        mock_instance = mock_processor.return_value
        mock_instance.find_files_without_metadata.return_value = [
            '/test/file1.jpg',
            '/test/file2.jpg'
        ]
        
        with self.runner.isolated_filesystem():
            # Create a test directory
            import os
            os.makedirs('test_dir')
            
            result = self.runner.invoke(main, ['scan', 'test_dir'])
            
            assert result.exit_code == 0
            assert 'Found 2 files without metadata:' in result.output
            assert '/test/file1.jpg' in result.output
            assert '/test/file2.jpg' in result.output

    @patch('svk_xmp.cli.commands.MetadataProcessor')
    def test_scan_command_no_files_found(self, mock_processor):
        """Test scan command when no files without metadata are found."""
        mock_instance = mock_processor.return_value
        mock_instance.find_files_without_metadata.return_value = []
        
        with self.runner.isolated_filesystem():
            # Create a test directory
            import os
            os.makedirs('test_dir')
            
            result = self.runner.invoke(main, ['scan', 'test_dir'])
            
            assert result.exit_code == 0
            assert 'No files without metadata found.' in result.output

    @patch('svk_xmp.cli.commands.MetadataProcessor')
    def test_scan_command_with_extensions(self, mock_processor):
        """Test scan command with custom extensions."""
        mock_instance = mock_processor.return_value
        mock_instance.find_files_without_metadata.return_value = []
        
        with self.runner.isolated_filesystem():
            # Create a test directory
            import os
            os.makedirs('test_dir')
            
            result = self.runner.invoke(main, ['scan', 'test_dir', '--extensions', '.png', '--extensions', '.tiff'])
            
            assert result.exit_code == 0
            mock_instance.find_files_without_metadata.assert_called_once_with('test_dir', ['.png', '.tiff'])

    @patch('svk_xmp.cli.commands.MetadataProcessor')
    def test_scan_command_error(self, mock_processor):
        """Test scan command with error handling."""
        mock_instance = mock_processor.return_value
        mock_instance.find_files_without_metadata.side_effect = MyProjectError("Test error")
        
        with self.runner.isolated_filesystem():
            # Create a test directory
            import os
            os.makedirs('test_dir')
            
            result = self.runner.invoke(main, ['scan', 'test_dir'])
            
            assert result.exit_code == 1
            assert 'Error: Test error' in result.output

    def test_scan_command_nonexistent_directory(self):
        """Test scan command with nonexistent directory."""
        result = self.runner.invoke(main, ['scan', 'nonexistent_dir'])
        assert result.exit_code == 2  # Click's exit code for invalid arguments

    @patch('svk_xmp.cli.commands.MetadataProcessor')
    def test_context_object_creation(self, mock_processor):
        """Test that context object is properly created and passed."""
        mock_instance = mock_processor.return_value
        mock_instance.extract_basic_info.return_value = {'filename': 'test.jpg'}
        
        with self.runner.isolated_filesystem():
            # Create a test file
            with open('test.jpg', 'w') as f:
                f.write('test')
            
            result = self.runner.invoke(main, ['--exiftool-path', '/custom/path', 'extract', 'test.jpg'])
            
            # Verify that MetadataProcessor was called with the correct path
            mock_processor.assert_called_with('/custom/path')
            assert result.exit_code == 0

    @patch('svk_xmp.cli.commands.MetadataProcessor')
    def test_context_object_none_path(self, mock_processor):
        """Test that context object handles None exiftool path."""
        mock_instance = mock_processor.return_value
        mock_instance.extract_basic_info.return_value = {'filename': 'test.jpg'}
        
        with self.runner.isolated_filesystem():
            # Create a test file
            with open('test.jpg', 'w') as f:
                f.write('test')
            
            result = self.runner.invoke(main, ['extract', 'test.jpg'])
            
            # Verify that MetadataProcessor was called with None
            mock_processor.assert_called_with(None)
            assert result.exit_code == 0