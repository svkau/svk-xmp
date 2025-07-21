"""Wrapper for exiftool command-line tool."""

import subprocess
import json
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Union
from .exceptions import ExifToolError, ExifToolNotFoundError


class ExifToolWrapper:
    """Wrapper class for exiftool operations."""

    def __init__(self, exiftool_path: Optional[str] = None):
        """Initialize with optional custom exiftool path."""
        self.exiftool_path = exiftool_path or "exiftool"
        self._verify_exiftool()

    def _verify_exiftool(self):
        """Verify that exiftool is available."""
        if not shutil.which(self.exiftool_path):
            raise ExifToolNotFoundError(
                f"exiftool not found. Please install exiftool or provide correct path."
            )

    def _run_command(self, args: List[str]) -> subprocess.CompletedProcess:
        """Run exiftool command with given arguments."""
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