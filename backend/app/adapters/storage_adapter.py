import os
import uuid
from abc import ABC, abstractmethod
from typing import Dict, Any
from backend.app.core.config import settings

class StorageAdapter(ABC):
    """
    Abstract storage adapter interface.
    Allows zero-cost switching between local filesystem and Google Drive.
    """
    @abstractmethod
    def save_file(self, file_bytes: bytes, filename: str) -> Dict[str, Any]:
        """Saves file and returns dictionary of metadata (e.g. local_path or gdrive_file_id/view_url)"""
        pass

    @abstractmethod
    def get_file(self, identifier: str) -> bytes:
        """Retrieves raw file bytes by path or cloud file ID"""
        pass

class LocalStorageAdapter(StorageAdapter):
    """
    Local filesystem storage adapter.
    Saves uploaded receipt files to the configured local folder.
    """
    def __init__(self, upload_dir: str | None = None):
        self.upload_dir = upload_dir or settings.LOCAL_STORAGE_DIR
        os.makedirs(self.upload_dir, exist_ok=True)

    def save_file(self, file_bytes: bytes, filename: str) -> Dict[str, Any]:
        ext = os.path.splitext(filename)[1]
        unique_name = f"{uuid.uuid4().hex}{ext}"
        destination_path = os.path.join(self.upload_dir, unique_name)

        with open(destination_path, "wb") as f:
            f.write(file_bytes)

        return {
            "file_name": filename,
            "local_path": destination_path,
            "gdrive_file_id": None,
            "gdrive_view_url": None,
        }

    def get_file(self, identifier: str) -> bytes:
        if not os.path.exists(identifier):
            raise FileNotFoundError(f"File not found on local storage: {identifier}")
        with open(identifier, "rb") as f:
            return f.read()

class GoogleDriveStorageAdapter(StorageAdapter):
    """
    Google Drive cloud storage adapter stub for Module 2.
    Will leverage Google Drive REST API to store receipt images at zero cost.
    """
    def __init__(self):
        pass

    def save_file(self, file_bytes: bytes, filename: str) -> Dict[str, Any]:
        raise NotImplementedError("GoogleDriveStorageAdapter is a stub in Module 1 and will be implemented in Module 2.")

    def get_file(self, identifier: str) -> bytes:
        raise NotImplementedError("GoogleDriveStorageAdapter is a stub in Module 1 and will be implemented in Module 2.")

def get_storage_adapter() -> StorageAdapter:
    """
    Factory function returning the configured storage adapter based on STORAGE_MODE env var.
    """
    if settings.STORAGE_MODE == "drive":
        return GoogleDriveStorageAdapter()
    return LocalStorageAdapter()
