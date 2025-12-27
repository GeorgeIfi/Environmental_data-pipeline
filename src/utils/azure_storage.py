from azure.storage.filedatalake import DataLakeServiceClient
from azure.core.exceptions import ResourceNotFoundError, HttpResponseError
import os


class AzureStorage:
    def __init__(self):
        account = os.getenv("AZURE_STORAGE_ACCOUNT")
        key = os.getenv("AZURE_STORAGE_KEY")
        container = os.getenv("AZURE_CONTAINER", "environmental-data")  # ADLS filesystem name

        # Fail fast with clear messages (prevents "none.dfs.core.windows.net")
        missing = []
        if not account:
            missing.append("AZURE_STORAGE_ACCOUNT")
        if not key:
            missing.append("AZURE_STORAGE_KEY")
        if missing:
            raise ValueError(
                f"Missing required environment variables: {', '.join(missing)}. "
                "Ensure your .env is loaded (e.g., using python-dotenv) or set them in the shell."
            )

        self.service_client = DataLakeServiceClient(
            account_url=f"https://{account}.dfs.core.windows.net",
            credential=key,
        )
        self.container = container

    def upload_file(self, local_path: str, remote_path: str):
        """
        Upload a local file to ADLS Gen2.
        container == ADLS filesystem name
        remote_path == path within the filesystem (e.g., 'silver/cleaned_data.parquet')
        """
        fs_client = self.service_client.get_file_system_client(self.container)

        # Optional: ensure filesystem exists (helpful in dev)
        try:
            fs_client.get_file_system_properties()
        except ResourceNotFoundError:
            # Create if missing (remove this if you prefer strict behavior)
            fs_client.create_file_system()

        file_client = fs_client.get_file_client(remote_path)

        try:
            with open(local_path, "rb") as data:
                file_client.upload_data(data, overwrite=True)
        except FileNotFoundError as e:
            raise FileNotFoundError(f"Local file not found: {local_path}") from e
        except HttpResponseError as e:
            # More actionable Azure error
            raise RuntimeError(
                f"Azure upload failed. Filesystem='{self.container}', remote_path='{remote_path}'. "
                f"Original error: {e.message if hasattr(e, 'message') else str(e)}"
            ) from e
