"""Wrapper for exiftool command-line tool."""

import subprocess
import json
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Union, Callable, Any
from .exceptions import ExifToolError, ExifToolNotFoundError


class ExifToolWrapper:
    """Wrapper class for exiftool operations."""

    def __init__(self, exiftool_path: Optional[str] = None, persistent: bool = False):
        """Initialize with optional custom exiftool path and persistent mode."""
        self.exiftool_path = exiftool_path or "exiftool"
        self.persistent = persistent
        self._process = None
        self._verify_exiftool()
        
        if persistent:
            self._start_persistent_process()

    def _start_persistent_process(self):
        """Start a persistent exiftool process."""
        try:
            self._process = subprocess.Popen([
                self.exiftool_path, 
                '-stay_open', 'True',
                '-@', '-',  # Read commands from stdin
                '-common_args',  # Arguments common to all commands
                '-charset', 'UTF8'  # Ensure UTF-8 output
            ], stdin=subprocess.PIPE, stdout=subprocess.PIPE, 
               stderr=subprocess.PIPE, text=True, bufsize=0)
        except Exception as e:
            raise ExifToolError(f"Failed to start persistent exiftool process: {e}")

    def _stop_persistent_process(self):
        """Stop the persistent exiftool process."""
        if self._process:
            try:
                self._process.stdin.write('-stay_open\nFalse\n')
                self._process.stdin.flush()
                self._process.wait(timeout=5)
            except Exception:
                self._process.terminate()
                self._process.wait()
            finally:
                self._process = None

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self._stop_persistent_process()

    def _verify_exiftool(self):
        """Verify that exiftool is available."""
        if not shutil.which(self.exiftool_path):
            raise ExifToolNotFoundError(
                f"exiftool not found. Please install exiftool or provide correct path."
            )

    def _run_command(self, args: List[str]) -> subprocess.CompletedProcess:
        """Run exiftool command with given arguments."""
        if self.persistent and self._process:
            return self._run_persistent_command(args)
        else:
            return self._run_direct_command(args)

    def _run_direct_command(self, args: List[str]) -> subprocess.CompletedProcess:
        """Run exiftool command directly (non-persistent mode)."""
        cmd = [self.exiftool_path] + args
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            return result
        except subprocess.CalledProcessError as e:
            raise ExifToolError(f"exiftool command failed: {e.stderr}")

    def _run_persistent_command(self, args: List[str]) -> subprocess.CompletedProcess:
        """Run exiftool command through persistent process."""
        if not self._process:
            raise ExifToolError("Persistent process not available")
        
        try:
            # Send command arguments
            command = '\n'.join(args) + '\n-execute\n'
            self._process.stdin.write(command)
            self._process.stdin.flush()
            
            # Read response until we get the ready marker
            stdout_lines = []
            stderr_lines = []
            
            while True:
                line = self._process.stdout.readline()
                if not line:
                    raise ExifToolError("Persistent process died unexpectedly")
                
                line = line.rstrip('\n')
                if line == '{ready}':
                    break
                elif line.startswith('{ready'):
                    # Sometimes ready comes with extra info
                    break
                else:
                    stdout_lines.append(line)
            
            # Read any stderr output (non-blocking)
            import select
            import sys
            if hasattr(select, 'select') and sys.platform != 'win32':
                # Unix-like systems
                ready, _, _ = select.select([self._process.stderr], [], [], 0.1)
                if ready:
                    while True:
                        ready, _, _ = select.select([self._process.stderr], [], [], 0.01)
                        if not ready:
                            break
                        line = self._process.stderr.readline()
                        if line:
                            stderr_lines.append(line.rstrip('\n'))
            
            stdout = '\n'.join(stdout_lines) + ('\n' if stdout_lines else '')
            stderr = '\n'.join(stderr_lines)
            
            # Create a mock CompletedProcess object
            class MockCompletedProcess:
                def __init__(self, stdout, stderr, returncode=0):
                    self.stdout = stdout
                    self.stderr = stderr
                    self.returncode = returncode
            
            result = MockCompletedProcess(stdout, stderr)
            
            # Check for errors in stderr
            if stderr and 'error' in stderr.lower():
                raise ExifToolError(f"exiftool command failed: {stderr}")
                
            return result
            
        except Exception as e:
            if "Persistent process died" in str(e):
                self._process = None
                raise ExifToolError(f"Persistent exiftool process failed: {e}")
            raise ExifToolError(f"Persistent command execution failed: {e}")

    def get_metadata(self, file_path: Union[str, Path]) -> Dict:
        """Extract metadata from a file."""
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        args = ["-j", "-G", str(file_path)]
        result = self._run_command(args)

        try:
            metadata = json.loads(result.stdout)
            return metadata[0] if metadata else {}
        except json.JSONDecodeError as e:
            raise ExifToolError(f"Failed to parse exiftool output: {e}")

    def set_metadata(self, file_path: Union[str, Path], metadata: Dict) -> bool:
        """Set metadata for a file."""
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        args = []
        for key, value in metadata.items():
            args.extend([f"-{key}={value}"])
        args.append(str(file_path))

        try:
            self._run_command(args)
            return True
        except ExifToolError:
            return False

    def remove_metadata(self, file_path: Union[str, Path], tags: Optional[List[str]] = None) -> bool:
        """Remove metadata from a file."""
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        if tags:
            args = [f"-{tag}=" for tag in tags]
        else:
            args = ["-all="]

        args.append(str(file_path))

        try:
            self._run_command(args)
            return True
        except ExifToolError:
            return False

    def copy_metadata(self, source: Union[str, Path], target: Union[str, Path]) -> bool:
        """Copy metadata from source to target file."""
        source_path = Path(source)
        target_path = Path(target)

        if not source_path.exists():
            raise FileNotFoundError(f"Source file not found: {source_path}")
        if not target_path.exists():
            raise FileNotFoundError(f"Target file not found: {target_path}")

        args = ["-TagsFromFile", str(source_path), str(target_path)]

        try:
            self._run_command(args)
            return True
        except ExifToolError:
            return False

    def backup_metadata_to_xml_string(self, file_path: Union[str, Path]) -> str:
        """Export all metadata from a file to XML string."""
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        args = ["-X", str(file_path)]
        result = self._run_command(args)
        return result.stdout

    def restore_metadata_from_xml_string(self, xml_string: str, target_path: Union[str, Path]) -> bool:
        """Restore metadata from XML string to target file."""
        import tempfile
        target_path = Path(target_path)
        
        if not target_path.exists():
            raise FileNotFoundError(f"Target file not found: {target_path}")

        # Create temporary XML file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False) as temp_file:
            temp_file.write(xml_string)
            temp_xml_path = temp_file.name

        try:
            args = ["-TagsFromFile", temp_xml_path, "-all:all", str(target_path)]
            self._run_command(args)
            return True
        except ExifToolError:
            return False
        finally:
            # Clean up temporary file
            Path(temp_xml_path).unlink(missing_ok=True)

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
        
        Args:
            path: File, directory, or zip file to process
            args_file: Path to exiftool arguments file for metadata synchronization
            file_extensions: List of file extensions to process (e.g., ['.jpg', '.jpeg'])
            recursive: Include subdirectories when processing directories
            verbose: Enable detailed output messages
            progress_callback: Optional callback function (current_file, current_index, total_files)
            
        Returns:
            Dictionary with processing results including processed files, errors, warnings, and summary
        """
        path = Path(path)
        args_file = Path(args_file)
        
        if not args_file.exists():
            raise FileNotFoundError(f"Arguments file not found: {args_file}")
            
        # Default image file extensions
        if file_extensions is None:
            file_extensions = ['.jpg', '.jpeg', '.jpe', '.tif', '.tiff', '.png', '.gif', '.bmp', '.webp']
        
        # Convert extensions to lowercase for comparison
        file_extensions = [ext.lower() for ext in file_extensions]
        
        # Initialize result structure
        result = {
            'processed': [],
            'errors': [],
            'warnings': [],
            'skipped': [],
            'summary': {
                'total_files': 0,
                'processed': 0,
                'errors': 0,
                'warnings': 0,
                'skipped': 0
            }
        }
        
        # Get list of files to process
        files_to_process = self._get_files_to_process(path, file_extensions, recursive)
        result['summary']['total_files'] = len(files_to_process)
        
        if verbose:
            print(f"Found {len(files_to_process)} files to process")
        
        # Process each file
        for index, file_path in enumerate(files_to_process):
            if progress_callback:
                progress_callback(str(file_path), index, len(files_to_process))
            
            try:
                self._sync_single_file(file_path, args_file, result, verbose)
            except Exception as e:
                error_msg = f"Unexpected error processing {file_path}: {str(e)}"
                result['errors'].append({'file': str(file_path), 'error': error_msg})
                result['summary']['errors'] += 1
                if verbose:
                    print(f"ERROR: {error_msg}")
        
        if not verbose:
            # Silent mode summary
            if result['summary']['errors'] > 0:
                print(f"Processing completed with {result['summary']['errors']} errors. Use verbose mode for details.")
            else:
                print(f"All {result['summary']['processed']} files processed successfully.")
        
        return result
    
    def _get_files_to_process(self, path: Path, file_extensions: List[str], recursive: bool) -> List[Path]:
        """Get list of image files to process from path (file, directory, or zip)."""
        files = []
        
        if not path.exists():
            raise FileNotFoundError(f"Path not found: {path}")
        
        if path.is_file():
            if path.suffix.lower() == '.zip':
                # Skip zip files - exiftool doesn't support writing to zip archives
                # This will be handled in processing to show as skipped with explanation
                files.append(path)
            elif path.suffix.lower() in file_extensions:
                files.append(path)
            else:
                # File with unsupported extension - will be skipped during processing
                files.append(path)
        elif path.is_dir():
            # Handle directory
            pattern = "**/*" if recursive else "*"
            for file_path in path.glob(pattern):
                if file_path.is_file() and file_path.suffix.lower() in file_extensions:
                    files.append(file_path)
        
        return sorted(files)
    
    
    def _sync_single_file(self, file_path: Union[Path, str], args_file: Path, result: Dict, verbose: bool):
        """Synchronize metadata for a single file."""
        file_str = str(file_path)
        
        # Check if file should be skipped based on extension
        if isinstance(file_path, Path):
            file_ext = file_path.suffix.lower()
        else:
            # Handle zip file entries (though we no longer process them)
            if '#' in file_str:
                file_ext = Path(file_str.split('#')[1]).suffix.lower()
            else:
                file_ext = Path(file_str).suffix.lower()
        
        # Skip zip files - exiftool doesn't support writing to zip archives
        if file_ext == '.zip':
            result['skipped'].append(file_str)
            result['summary']['skipped'] += 1
            if verbose:
                print(f"SKIPPED: {file_str} (zip files not supported - exiftool cannot write to zip archives)")
            return
        
        # Skip non-image files
        image_extensions = ['.jpg', '.jpeg', '.jpe', '.tif', '.tiff', '.png', '.gif', '.bmp', '.webp']
        if file_ext not in image_extensions:
            result['skipped'].append(file_str)
            result['summary']['skipped'] += 1
            if verbose:
                print(f"SKIPPED: {file_str} (unsupported file type)")
            return
        
        try:
            # First, validate the file
            self._validate_file(file_path)
            
            # Perform metadata synchronization
            args = ["-@", str(args_file), "-overwrite_original", file_str]
            process_result = self._run_command(args)
            
            # Check for warnings in output
            if process_result.stderr:
                # Parse stderr for warnings vs errors
                stderr_lines = process_result.stderr.strip().split('\n')
                has_errors = False
                warning_msgs = []
                
                for line in stderr_lines:
                    if line.strip():
                        if 'warning' in line.lower():
                            warning_msgs.append(line.strip())
                        else:
                            # Treat as error if not explicitly a warning
                            has_errors = True
                            result['errors'].append({'file': file_str, 'error': line.strip()})
                            result['summary']['errors'] += 1
                            if verbose:
                                print(f"ERROR in {file_str}: {line.strip()}")
                
                if warning_msgs:
                    for warning in warning_msgs:
                        result['warnings'].append({'file': file_str, 'warning': warning})
                        result['summary']['warnings'] += 1
                        if verbose:
                            print(f"WARNING in {file_str}: {warning}")
                
                if has_errors:
                    return
            
            # If we get here, processing was successful
            result['processed'].append(file_str)
            result['summary']['processed'] += 1
            
            if verbose:
                print(f"Processed: {file_str}")
                
        except ExifToolError as e:
            result['errors'].append({'file': file_str, 'error': str(e)})
            result['summary']['errors'] += 1
            if verbose:
                print(f"ERROR in {file_str}: {str(e)}")
    
    def _validate_file(self, file_path: Union[Path, str]):
        """Validate file using exiftool's -validate option."""
        file_str = str(file_path)
        
        try:
            args = ["-validate", "-warning", file_str]
            result = self._run_command(args)
            
            # If there's output in stderr, it indicates validation issues
            if result.stderr and result.stderr.strip():
                # Check if it's an error or just warnings
                stderr_lower = result.stderr.lower()
                if 'error' in stderr_lower and 'warning' not in stderr_lower:
                    raise ExifToolError(f"File validation failed: {result.stderr.strip()}")
                # If it's just warnings, we continue (as per requirements)
                
        except subprocess.CalledProcessError as e:
            raise ExifToolError(f"File validation failed: {e.stderr}")

    def batch_get_metadata(self, file_paths: List[Union[str, Path]]) -> List[Dict]:
        """Extract metadata from multiple files efficiently."""
        if not file_paths:
            return []
        
        # Convert all paths to strings
        str_paths = [str(Path(p)) for p in file_paths]
        
        # Check that all files exist
        for path in str_paths:
            if not Path(path).exists():
                raise FileNotFoundError(f"File not found: {path}")
        
        args = ["-j", "-G"] + str_paths
        result = self._run_command(args)
        
        try:
            metadata_list = json.loads(result.stdout)
            return metadata_list if metadata_list else []
        except json.JSONDecodeError as e:
            raise ExifToolError(f"Failed to parse exiftool output: {e}")

    def batch_extract_xmp_xml(self, file_paths: List[Union[str, Path]]) -> Dict[str, str]:
        """Extract XMP XML from multiple files efficiently."""
        if not file_paths:
            return {}
        
        results = {}
        
        # For batch operations, we need to process files individually for XMP
        # because exiftool doesn't provide a clean way to separate XMP output for multiple files
        for file_path in file_paths:
            try:
                xmp_xml = self.extract_xmp_xml(file_path)
                results[str(file_path)] = xmp_xml
            except Exception as e:
                results[str(file_path)] = ""  # Empty string for files with no XMP or errors
        
        return results

    def extract_xmp_packet(self, file_path: Union[str, Path]) -> str:
        """Extract full XMP packet (use temporary file approach to get properly formatted packet)."""
        import tempfile
        import os
        
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        # Create temporary XMP file using -tagsfromfile approach
        with tempfile.NamedTemporaryFile(mode='w+', suffix='.xmp', delete=False) as temp_file:
            temp_xmp_path = temp_file.name

        try:
            # Use -tagsfromfile to write XMP to temporary file
            args = ["-tagsfromfile", str(file_path), "-xmp", temp_xmp_path]
            result = self._run_command(args)
            
            # Read the generated XMP file
            if os.path.exists(temp_xmp_path) and os.path.getsize(temp_xmp_path) > 0:
                with open(temp_xmp_path, 'r', encoding='utf-8', errors='replace') as f:
                    content = f.read()
                
                # Clean up excessive whitespace before the end packet
                import re
                # Replace multiple whitespace characters before <?xpacket end with just a newline
                content = re.sub(r'\s+(?=<\?xpacket end)', '\n', content)
                
                return content
            else:
                return ""
            
        except ExifToolError as e:
            # Check if error is because no XMP data exists  
            if "no xmp" in str(e).lower() or "warning" in str(e).lower():
                return ""
            raise e
        finally:
            # Clean up temporary file
            if os.path.exists(temp_xmp_path):
                os.unlink(temp_xmp_path)

    def extract_xmp_xml(self, file_path: Union[str, Path]) -> str:
        """Extract clean XMP XML (just <x:xmpmeta> content) from a file."""
        xmp_packet = self.extract_xmp_packet(file_path)
        if not xmp_packet:
            return ""
        
        # Extract content between <x:xmpmeta> tags
        import re
        match = re.search(r'(<x:xmpmeta.*?</x:xmpmeta>)', xmp_packet, re.DOTALL)
        if match:
            return match.group(1)
        return ""