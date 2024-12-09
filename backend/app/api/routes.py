from fastapi import APIRouter, HTTPException
from backend.app.models.schemas import ProjectSetup, DocumentationUpdate
from backend.app.core.data_manager import GitHubRepoManager
from backend.app.core.chunker import UniversalFileChunker
from backend.app.core.embedder import build_batch_embedder_from_flags
import logging


router = APIRouter()


@router.post("/setup")
async def setup_project(project: ProjectSetup):
    """Initialize project repositories and setup monitoring"""
    try:
        print('project: ', project.code_repo.url)
        code_args = {
            "repo_id": project.code_repo.url,
            "local_dir": project.code_repo.url,   
            "commit_hash": None,
            "access_token": None,
            "inclusion_file": None,
            "exclusion_file": None,
            "embedding_provider": "openai",
            "embedding_model": "text-embedding-3-large",
            "embedding_size": 3072
        }

        # logging.info("initializing code repo manager")
        code_repo_manager = GitHubRepoManager.from_args(code_args)
        code_chunker = UniversalFileChunker(max_tokens=2000)
        code_repo_embedder = build_batch_embedder_from_flags(code_repo_manager, code_chunker, code_args)
        repo_jobs_file = code_repo_embedder.embed_dataset(64, 100)
        print("code_repo_manager: ", code_repo_manager)


        docs_repo_id = project.docs_repo.url
        docs_branch = project.docs_repo.branch
        docs_folder_path = project.docs_repo.folder_path
        return {"message": "Project setup successful"}
    except Exception as e:
        print(e)
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/changes")
async def get_recent_changes():
    """Get recent code changes and their impact on documentation"""
    try:
        return ""
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/update-documentation")
async def update_documentation(update: DocumentationUpdate):
    """Create PR with documentation updates"""
    try:

        return {"pr_url"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 