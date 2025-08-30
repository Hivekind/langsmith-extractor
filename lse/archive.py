"""Archive utilities for trace backup and restore operations."""

import logging
import zipfile
from pathlib import Path
from typing import List, Optional

from lse.config import Settings
from lse.exceptions import LSEError

logger = logging.getLogger(__name__)


class ArchiveError(LSEError):
    """Error occurred during archive operations."""

    pass


class ArchiveManager:
    """Handles archive operations for trace data."""

    def __init__(self, settings: Settings):
        """Initialize archive manager.

        Args:
            settings: Application settings
        """
        self.settings = settings
        self.output_dir = Path(settings.output_dir)

    def get_trace_folder(self, project_name: str, date: str) -> Path:
        """Get the folder path for traces of a specific project and date.

        Args:
            project_name: Project name
            date: Date in YYYY-MM-DD format

        Returns:
            Path to the trace folder
        """
        # Sanitize project name for filesystem
        safe_project = "".join(c for c in project_name if c.isalnum() or c in "-_.")
        return self.output_dir / safe_project / date

    def validate_trace_folder(self, project_name: str, date: str) -> None:
        """Validate that a trace folder exists and contains traces.

        Args:
            project_name: Project name
            date: Date in YYYY-MM-DD format

        Raises:
            ArchiveError: If folder doesn't exist or is empty
        """
        folder_path = self.get_trace_folder(project_name, date)

        if not folder_path.exists():
            raise ArchiveError(
                f"No trace folder found for {project_name} on {date}. "
                f"Expected folder: {folder_path}"
            )

        # Check for JSON files (excluding summary files)
        json_files = [f for f in folder_path.glob("*.json") if not f.name.startswith("_")]

        if not json_files:
            raise ArchiveError(
                f"No trace files found in {folder_path}. "
                "Run 'lse fetch' first to fetch traces for this date."
            )

    def create_zip_filename(self, project_name: str, date: str) -> str:
        """Create standardized zip filename.

        Args:
            project_name: Project name
            date: Date in YYYY-MM-DD format

        Returns:
            Zip filename in format: [project-name]_[date].zip
        """
        # Sanitize project name for filename
        safe_project = "".join(c for c in project_name if c.isalnum() or c in "-_.")
        return f"{safe_project}_{date}.zip"

    def create_zip_archive(
        self, project_name: str, date: str, output_dir: Optional[Path] = None
    ) -> Path:
        """Create a zip archive of traces for a specific date.

        Args:
            project_name: Project name
            date: Date in YYYY-MM-DD format
            output_dir: Directory to save zip file (defaults to ./archives)

        Returns:
            Path to created zip file

        Raises:
            ArchiveError: If zip creation fails
        """
        try:
            # Validate input
            self.validate_trace_folder(project_name, date)

            # Set up output directory
            if output_dir is None:
                output_dir = Path("./archives")
            output_dir.mkdir(parents=True, exist_ok=True)

            # Create zip file path
            zip_filename = self.create_zip_filename(project_name, date)
            zip_path = output_dir / zip_filename

            # Get source folder
            source_folder = self.get_trace_folder(project_name, date)

            logger.info(f"Creating zip archive: {zip_path}")
            logger.info(f"Source folder: {source_folder}")

            # Create zip archive with flat structure
            with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
                # Add all JSON files to zip (flat structure)
                json_files = list(source_folder.glob("*.json"))
                total_files = len(json_files)

                for i, file_path in enumerate(json_files):
                    # Use just the filename (flat structure in zip)
                    arcname = file_path.name
                    zf.write(file_path, arcname)
                    logger.debug(f"Added to zip: {arcname} [{i + 1}/{total_files}]")

            logger.info(f"Successfully created zip archive: {zip_path}")
            logger.info(f"Archive contains {total_files} files")

            return zip_path

        except Exception as e:
            raise ArchiveError(f"Failed to create zip archive: {e}") from e

    def extract_zip_archive(
        self, zip_path: Path, project_name: str, date: str, force: bool = False
    ) -> Path:
        """Extract a zip archive to the appropriate trace folder.

        Args:
            zip_path: Path to zip file
            project_name: Project name
            date: Date in YYYY-MM-DD format
            force: Skip confirmation if folder already exists

        Returns:
            Path to extracted folder

        Raises:
            ArchiveError: If extraction fails
        """
        try:
            if not zip_path.exists():
                raise ArchiveError(f"Zip file not found: {zip_path}")

            # Get target folder
            target_folder = self.get_trace_folder(project_name, date)

            # Check if target folder exists
            if target_folder.exists() and not force:
                existing_files = list(target_folder.glob("*.json"))
                if existing_files:
                    raise ArchiveError(
                        f"Target folder {target_folder} already contains {len(existing_files)} files. "
                        "Use --force flag to overwrite, or remove the existing folder first."
                    )

            # Create target folder
            target_folder.mkdir(parents=True, exist_ok=True)

            logger.info(f"Extracting zip archive: {zip_path}")
            logger.info(f"Target folder: {target_folder}")

            # Extract zip contents
            with zipfile.ZipFile(zip_path, "r") as zf:
                file_list = zf.namelist()
                json_files = [f for f in file_list if f.endswith(".json")]

                for filename in json_files:
                    # Extract to target folder
                    zf.extract(filename, target_folder)
                    logger.debug(f"Extracted: {filename}")

            logger.info(f"Successfully extracted {len(json_files)} files to {target_folder}")

            return target_folder

        except Exception as e:
            raise ArchiveError(f"Failed to extract zip archive: {e}") from e

    def list_local_archives(self, project_name: str) -> List[str]:
        """List available dates for which traces exist locally.

        Args:
            project_name: Project name

        Returns:
            List of dates (YYYY-MM-DD format) with available traces
        """
        # Sanitize project name
        safe_project = "".join(c for c in project_name if c.isalnum() or c in "-_.")
        project_folder = self.output_dir / safe_project

        if not project_folder.exists():
            return []

        # Find date folders with JSON files
        available_dates = []
        for date_folder in project_folder.iterdir():
            if date_folder.is_dir() and date_folder.name.count("-") == 2:
                # Check if folder contains JSON files
                json_files = [f for f in date_folder.glob("*.json") if not f.name.startswith("_")]
                if json_files:
                    available_dates.append(date_folder.name)

        return sorted(available_dates)

    def get_archive_stats(self, project_name: str, date: str) -> dict:
        """Get statistics about a trace archive.

        Args:
            project_name: Project name
            date: Date in YYYY-MM-DD format

        Returns:
            Dictionary with archive statistics
        """
        try:
            folder_path = self.get_trace_folder(project_name, date)

            if not folder_path.exists():
                return {"exists": False}

            # Count files
            json_files = [f for f in folder_path.glob("*.json") if not f.name.startswith("_")]
            summary_files = list(folder_path.glob("_*.json"))

            # Calculate total size
            total_size = sum(f.stat().st_size for f in json_files)

            return {
                "exists": True,
                "folder_path": str(folder_path),
                "trace_files": len(json_files),
                "summary_files": len(summary_files),
                "total_size_bytes": total_size,
                "total_size_mb": round(total_size / (1024 * 1024), 2),
            }

        except Exception as e:
            logger.warning(f"Failed to get archive stats: {e}")
            return {"exists": False, "error": str(e)}
