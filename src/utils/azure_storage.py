from azure.storage.filedatalake import DataLakeServiceClient
import os

class AzureStorage:
    def __init__(self):
        self.service_client = DataLakeServiceClient(
            account_url=f"https://{os.getenv('AZURE_STORAGE_ACCOUNT')}.dfs.core.windows.net",
            credential=os.getenv('AZURE_STORAGE_KEY')
        )
        self.container = os.getenv('AZURE_CONTAINER', 'environmental-data')
    
    def upload_file(self, local_path: str, remote_path: str):
        file_client = self.service_client.get_file_client(
            file_system=self.container, 
            file_path=remote_path
        )
        with open(local_path, 'rb') as data:
            file_client.upload_data(data, overwrite=True)