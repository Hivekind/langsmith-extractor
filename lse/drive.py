"""Google Drive integration for archive storage."""

import logging
import re
from pathlib import Path
from typing import List

from lse.config import Settings
from lse.exceptions import LSEError

logger = logging.getLogger(__name__)


class DriveError(LSEError):
    """Error occurred during Google Drive operations."""

    pass


class GoogleDriveClient:
    """Google Drive client for archive operations."""

    def __init__(self, settings: Settings):
        """Initialize Google Drive client.

        Args:
            settings: Application settings with Drive configuration
        """
        self.settings = settings
        self._service = None
        self._folder_id = None

    def _get_folder_id_from_url(self, url: str) -> str:
        """Extract folder ID from Google Drive URL.

        Args:
            url: Google Drive folder URL

        Returns:
            Folder ID string

        Raises:
            DriveError: If URL format is invalid
        """
        # Support various Google Drive URL formats:
        # https://drive.google.com/drive/folders/FOLDER_ID
        # https://drive.google.com/drive/folders/FOLDER_ID?usp=sharing
        # https://drive.google.com/open?id=FOLDER_ID

        folder_id_patterns = [
            r"/folders/([a-zA-Z0-9_-]+)",  # Standard folder URL
            r"[?&]id=([a-zA-Z0-9_-]+)",  # Open URL format
        ]

        for pattern in folder_id_patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)

        raise DriveError(f"Invalid Google Drive folder URL format: {url}")

    def _initialize_service(self):
        """Initialize Google Drive API service."""
        if self._service is not None:
            return

        try:
            from google.oauth2.credentials import Credentials
            from google.oauth2.service_account import Credentials as ServiceAccountCredentials
            from google.auth.transport.requests import Request
            from google_auth_oauthlib.flow import InstalledAppFlow
            from googleapiclient.discovery import build

            # Validate configuration
            if not self.settings.google_drive_folder_url:
                raise DriveError(
                    "Google Drive folder URL is required. "
                    "Set GOOGLE_DRIVE_FOLDER_URL in your .env file."
                )

            # Extract folder ID from URL
            self._folder_id = self._get_folder_id_from_url(self.settings.google_drive_folder_url)

            # Set up authentication based on auth type
            scopes = ["https://www.googleapis.com/auth/drive.file"]
            creds = None

            if self.settings.google_drive_auth_type == "service_account":
                # Service account authentication
                if not self.settings.google_drive_credentials_path:
                    raise DriveError(
                        "Service account credentials path is required when using service_account auth. "
                        "Set GOOGLE_DRIVE_CREDENTIALS_PATH in your .env file."
                    )

                if not self.settings.google_drive_credentials_path.exists():
                    raise DriveError(
                        f"Service account credentials file not found: "
                        f"{self.settings.google_drive_credentials_path}"
                    )

                creds = ServiceAccountCredentials.from_service_account_file(
                    str(self.settings.google_drive_credentials_path), scopes=scopes
                )

            else:  # oauth2
                # OAuth2 user authentication
                token_path = Path("token.json")
                credentials_path = self.settings.google_drive_credentials_path or Path(
                    "credentials.json"
                )

                # Load existing token if available
                if token_path.exists():
                    creds = Credentials.from_authorized_user_file(str(token_path), scopes)

                # If there are no (valid) credentials available, let the user log in
                if not creds or not creds.valid:
                    if creds and creds.expired and creds.refresh_token:
                        creds.refresh(Request())
                    else:
                        if not credentials_path.exists():
                            raise DriveError(
                                f"OAuth2 credentials file not found: {credentials_path}. "
                                "Download it from Google Cloud Console and save as credentials.json"
                            )

                        flow = InstalledAppFlow.from_client_secrets_file(
                            str(credentials_path), scopes
                        )
                        creds = flow.run_local_server(port=0)

                    # Save the credentials for the next run
                    with open(token_path, "w") as token:
                        token.write(creds.to_json())

            # Build the service
            self._service = build("drive", "v3", credentials=creds)
            logger.info(
                f"Initialized Google Drive service with {self.settings.google_drive_auth_type} auth"
            )

        except ImportError as e:
            raise DriveError(
                "Google Drive dependencies not found. Run 'uv sync' to install required packages."
            ) from e
        except Exception as e:
            raise DriveError(f"Failed to initialize Google Drive service: {e}") from e

    def _ensure_project_folder(self, project_name: str) -> str:
        """Ensure project subfolder exists in the Drive folder.

        Args:
            project_name: Project name for subfolder

        Returns:
            Project folder ID

        Raises:
            DriveError: If folder creation fails
        """
        try:
            # Search for existing project folder
            query = f"'{self._folder_id}' in parents and name='{project_name}' and trashed=false"
            results = self._service.files().list(q=query, fields="files(id, name)").execute()
            items = results.get("files", [])

            if items:
                # Project folder exists
                project_folder_id = items[0]["id"]
                logger.debug(f"Found existing project folder: {project_name} ({project_folder_id})")
                return project_folder_id

            # Create project folder
            folder_metadata = {
                "name": project_name,
                "parents": [self._folder_id],
                "mimeType": "application/vnd.google-apps.folder",
            }

            folder = self._service.files().create(body=folder_metadata, fields="id").execute()

            project_folder_id = folder.get("id")
            logger.info(f"Created project folder: {project_name} ({project_folder_id})")
            return project_folder_id

        except Exception as e:
            raise DriveError(f"Failed to ensure project folder '{project_name}': {e}") from e

    def list_project_archives(self, project_name: str) -> List[dict]:
        """List available archive files for a project.

        Args:
            project_name: Project name

        Returns:
            List of archive file info dictionaries

        Raises:
            DriveError: If listing fails
        """
        try:
            self._initialize_service()
            project_folder_id = self._ensure_project_folder(project_name)

            # List zip files in project folder
            query = f"'{project_folder_id}' in parents and name contains '.zip' and trashed=false"
            results = (
                self._service.files()
                .list(q=query, fields="files(id, name, size, createdTime, modifiedTime)")
                .execute()
            )

            archives = []
            for file in results.get("files", []):
                archives.append(
                    {
                        "id": file["id"],
                        "name": file["name"],
                        "size": int(file.get("size", 0)),
                        "created": file["createdTime"],
                        "modified": file["modifiedTime"],
                    }
                )

            return sorted(archives, key=lambda x: x["name"])

        except Exception as e:
            raise DriveError(f"Failed to list archives for project '{project_name}': {e}") from e

    def upload_archive(self, file_path: Path, project_name: str, force: bool = False) -> str:
        """Upload archive file to Google Drive.

        Args:
            file_path: Path to zip file to upload
            project_name: Project name for organization
            force: Skip confirmation if file already exists

        Returns:
            File ID of uploaded file

        Raises:
            DriveError: If upload fails
        """
        try:
            self._initialize_service()

            if not file_path.exists():
                raise DriveError(f"Archive file not found: {file_path}")

            project_folder_id = self._ensure_project_folder(project_name)
            filename = file_path.name

            # Check if file already exists
            query = f"'{project_folder_id}' in parents and name='{filename}' and trashed=false"
            results = self._service.files().list(q=query, fields="files(id, name)").execute()
            existing_files = results.get("files", [])

            if existing_files and not force:
                raise DriveError(
                    f"File '{filename}' already exists on Google Drive. "
                    "Use --force flag to overwrite."
                )

            # Upload or update file
            from googleapiclient.http import MediaFileUpload

            media = MediaFileUpload(str(file_path), mimetype="application/zip", resumable=True)

            if existing_files:
                # Update existing file
                file_id = existing_files[0]["id"]
                updated_file = (
                    self._service.files()
                    .update(fileId=file_id, media_body=media, fields="id")
                    .execute()
                )

                logger.info(f"Updated existing file on Google Drive: {filename}")
                return updated_file.get("id")
            else:
                # Create new file
                file_metadata = {"name": filename, "parents": [project_folder_id]}

                uploaded_file = (
                    self._service.files()
                    .create(body=file_metadata, media_body=media, fields="id")
                    .execute()
                )

                logger.info(f"Uploaded new file to Google Drive: {filename}")
                return uploaded_file.get("id")

        except Exception as e:
            raise DriveError(f"Failed to upload archive '{file_path.name}': {e}") from e

    def download_archive(self, filename: str, project_name: str, output_path: Path) -> Path:
        """Download archive file from Google Drive.

        Args:
            filename: Name of archive file to download
            project_name: Project name
            output_path: Local path to save file

        Returns:
            Path to downloaded file

        Raises:
            DriveError: If download fails
        """
        try:
            self._initialize_service()
            project_folder_id = self._ensure_project_folder(project_name)

            # Find the file
            query = f"'{project_folder_id}' in parents and name='{filename}' and trashed=false"
            results = self._service.files().list(q=query, fields="files(id, name)").execute()
            files = results.get("files", [])

            if not files:
                raise DriveError(f"Archive '{filename}' not found in project '{project_name}'")

            file_id = files[0]["id"]

            # Download file
            from googleapiclient.http import MediaIoBaseDownload
            import io

            request = self._service.files().get_media(fileId=file_id)
            file_content = io.BytesIO()
            downloader = MediaIoBaseDownload(file_content, request)

            done = False
            while done is False:
                status, done = downloader.next_chunk()
                logger.debug(f"Download progress: {int(status.progress() * 100)}%")

            # Save to file
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "wb") as f:
                f.write(file_content.getvalue())

            logger.info(f"Downloaded archive from Google Drive: {output_path}")
            return output_path

        except Exception as e:
            raise DriveError(f"Failed to download archive '{filename}': {e}") from e

    def validate_configuration(self) -> dict:
        """Validate Google Drive configuration.

        Returns:
            Dictionary with validation results

        Raises:
            DriveError: If configuration is invalid
        """
        try:
            if not self.settings.google_drive_folder_url:
                raise DriveError("Google Drive folder URL is not configured")

            # Test folder ID extraction
            folder_id = self._get_folder_id_from_url(self.settings.google_drive_folder_url)

            # Test service initialization
            self._initialize_service()

            # Test folder access
            folder_info = (
                self._service.files()
                .get(fileId=self._folder_id, fields="id, name, permissions")
                .execute()
            )

            return {
                "valid": True,
                "folder_id": folder_id,
                "folder_name": folder_info.get("name"),
                "auth_type": self.settings.google_drive_auth_type,
            }

        except Exception as e:
            return {
                "valid": False,
                "error": str(e),
            }
