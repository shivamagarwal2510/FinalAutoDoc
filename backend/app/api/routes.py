from fastapi import APIRouter, HTTPException
from backend.app.models.schemas import ProjectSetup, DocumentationUpdate
from backend.app.core.data_manager import GitHubRepoManager
from backend.app.core.chunker import UniversalFileChunker
from backend.app.core.embedder import build_batch_embedder_from_flags
from backend.app.core.vector_store import build_vector_store_from_args
import os
import time
import re


router = APIRouter()
def sanitize_repo_url(repo_url: str) -> str:
    # Use regex to remove all non-alphabetic characters and convert to lowercase
    sanitized_url = re.sub(r'[^a-zA-Z]', '', repo_url).lower()
    return sanitized_url

@router.post("/setup")
async def setup_project(project: ProjectSetup):
    """Initialize project repositories and setup monitoring"""
    try:
        # Create base directory for repositories
        base_dir = os.path.join(os.getcwd(), "extractedRepos")
        
        # Create repo-specific directory
        repo_name = project.code_repo.url.split('/')[0]  # Get 'shadcn-ui' from 'shadcn-ui/ui'
        repo_dir = os.path.join(base_dir, repo_name.replace('-', '_'))  # shadcn_ui
        
        print('project: ', project.code_repo.url)
        code_args = {
            "repo_id": project.code_repo.url,
            "local_dir": os.path.join(repo_dir, project.code_repo.url.split('/')[1] + "codebase"),   
            "commit_hash": None,
            "access_token": None,
            "inclusion_file": None,
            "exclusion_file": None,
            "embedding_provider": "openai",
            "embedding_model": "text-embedding-3-large",
            "embedding_size": 3072,
            "vector_store_provider":"pinecone",
            "index_namespace": "code"+sanitize_repo_url(project.code_repo.url),
            "retrieval_alpha": 0.9,
            "index_name": "code"+sanitize_repo_url(project.code_repo.url)+"embeddings",
        }

        # logging.info("initializing code repo manager")
        code_repo_manager = GitHubRepoManager.from_args(code_args)
        # code_chunker = UniversalFileChunker(max_tokens=1000)
        # code_repo_embedder = build_batch_embedder_from_flags(code_repo_manager, code_chunker, code_args)
        # repo_jobs_file = code_repo_embedder.embed_dataset(20, 500)
        # print("repo_jobs_file: ", repo_jobs_file)
        # if code_repo_embedder is not None:
        #     print("Waiting for Repo Embeddings to be ready...")
        #     while not code_repo_embedder.embeddings_are_ready(repo_jobs_file):
        #         print("Sleeping for 30 seconds...")
        #         time.sleep(30)
        #     print("Repo Embeddings are ready!")
        #     repo_vector_store = build_vector_store_from_args(code_args, code_repo_manager)
        #     repo_vector_store.ensure_exists()
        #     repo_vector_store.upsert(code_repo_embedder.download_embeddings(repo_jobs_file), namespace=code_args["index_namespace"])

        doc_args = {
            "repo_id": project.docs_repo.url,
            "local_dir": os.path.join(repo_dir, project.docs_repo.url.split('/')[1] + "documentation"),   
            "commit_hash": None,
            "access_token": None,
            "inclusion_file": None,
            "exclusion_file": None,
            "doc_target_path": project.docs_repo.folder_path,
            "embedding_provider": "openai",
            "embedding_model": "text-embedding-3-large",
            "embedding_size": 3072,
            "vector_store_provider":"pinecone",
            "index_namespace": "doc"+sanitize_repo_url(project.docs_repo.url),
            "retrieval_alpha": 0.9,
            "index_name": "docembeddings",
        }
        print("doc_target_path: ", project.docs_repo.folder_path)
        docs_repo_manager = GitHubRepoManager.from_args(doc_args)
        print("docs_repo_manager: ", docs_repo_manager)

        doc_chunker = UniversalFileChunker(max_tokens=500)  # Smaller chunks for documentation
        doc_repo_embedder = build_batch_embedder_from_flags(docs_repo_manager, doc_chunker, doc_args)
        
        # Create embeddings for documentation
        doc_jobs_file = doc_repo_embedder.embed_dataset(20, 500)
        if doc_repo_embedder is not None:
            print("Waiting for Documentation Embeddings to be ready...")
            while not doc_repo_embedder.embeddings_are_ready(doc_jobs_file):
                print("Sleeping for 30 seconds...")
                time.sleep(30)
            print("Documentation Embeddings are ready!")
            docs_vector_store = build_vector_store_from_args(doc_args, docs_repo_manager)
            docs_vector_store.ensure_exists()
            docs_vector_store.upsert(doc_repo_embedder.download_embeddings(doc_jobs_file), namespace=doc_args["index_namespace"])


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