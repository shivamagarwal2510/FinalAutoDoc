from pymongo import MongoClient
from typing import Optional, Dict, Any
import os

class MongoDB:
    def __init__(self):
        connection_string = os.getenv("MONGO_CONNECTION_STRING")
        print("connection_string: ", connection_string)
        if not connection_string:
            raise ValueError(
                "MONGODB_CONNECTION_STRING environment variable is not set. "
                "Please set it in your .env file"
            )
            
        try:
            self.client = MongoClient(connection_string)
            # Test the connection
            self.client.admin.command('ping')
            self.db = self.client['docuflow']
            self.projects = self.db['projects']
        except Exception as e:
            raise ConnectionError(f"Failed to connect to MongoDB: {str(e)}")

    def create_project(self, code_repo_id: str, docs_repo_id: str, docs_folder_path: str) -> None:
        """Create or update a project mapping"""
        project = {
            "code_repo_id": code_repo_id,
            "docs_repo_id": docs_repo_id,
            "docs_folder_path": docs_folder_path
        }
        self.projects.update_one(
            {"code_repo_id": code_repo_id},
            {"$set": project},
            upsert=True
        )

    def get_project_by_code_repo(self, code_repo_id: str) -> Optional[Dict[str, Any]]:
        """Get project details by code repository ID"""
        return self.projects.find_one({"code_repo_id": code_repo_id}) 