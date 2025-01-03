from fastapi import APIRouter, HTTPException
from backend.app.models.schemas import ProjectSetup, DocumentationUpdate, CodeChangesRequest
from backend.app.core.data_manager import GitHubRepoManager
from backend.app.core.chunker import UniversalFileChunker
from backend.app.core.embedder import build_batch_embedder_from_flags
from backend.app.core.vector_store import build_vector_store_from_args
from backend.app.core.documentation_updater import build_documentation_update_chain
from backend.app.utils.xmlParser import extract_documentation_changes
from backend.app.core.mongodb import MongoDB
import os
import time
import re


router = APIRouter()

# Initialize MongoDB with your connection string
mongodb = MongoDB()

def sanitize_repo_url(repo_url: str) -> str:
    # Use regex to remove all non-alphabetic characters and convert to lowercase
    sanitized_url = re.sub(r'[^a-zA-Z]', '', repo_url).lower()
    return sanitized_url

@router.post("/setup")
async def setup_project(project: ProjectSetup):
    """Initialize project repositories and setup monitoring"""
    try:
        # Store project mapping in MongoDB
        mongodb.create_project(
            code_repo_id=project.code_repo.url,
            docs_repo_id=project.docs_repo.url,
            docs_folder_path=project.docs_repo.folder_path
        )

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
            "index_name": "codeembeddings",
        }

        # logging.info("initializing code repo manager")
        code_repo_manager = GitHubRepoManager.from_args(code_args)
        print("code_repo_manager: ", code_repo_manager)
        code_chunker = UniversalFileChunker(max_tokens=1000)
        code_repo_embedder = build_batch_embedder_from_flags(code_repo_manager, code_chunker, code_args)
        repo_jobs_file = code_repo_embedder.embed_dataset(20, 500)
        print("repo_jobs_file: ", repo_jobs_file)
        if code_repo_embedder is not None:
            print("Waiting for Repo Embeddings to be ready...")
            while not code_repo_embedder.embeddings_are_ready(repo_jobs_file):
                print("Sleeping for 30 seconds...")
                time.sleep(30)
            print("Repo Embeddings are ready!")
            repo_vector_store = build_vector_store_from_args(code_args, code_repo_manager)
            repo_vector_store.ensure_exists()
            repo_vector_store.upsert(code_repo_embedder.download_embeddings(repo_jobs_file), namespace=code_args["index_namespace"])

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

@router.post("/changes")
async def get_recent_changes(project: CodeChangesRequest):
    """Get recent code changes and their impact on documentation"""
    try:
        # Get project details from MongoDB
        project_details = mongodb.get_project_by_code_repo(project.code_repo_id)
        if not project_details:
            raise HTTPException(
                status_code=404, 
                detail="Project not found"
            )

        # Update project with MongoDB data
        project.docs_repo_id = project_details["docs_repo_id"]

        print("changes route: project: ", project)
        # Reuse the same arguments from setup
        code_args = {
            "repo_id": project.code_repo_id,
            "embedding_provider": "openai",
            "embedding_model": "text-embedding-3-large",
            "vector_store_provider": "pinecone",
            "index_namespace": "code"+sanitize_repo_url(project.code_repo_id),
            "index_name": "codeembeddings",
            "llm_provider": "anthropic",
            "llm_model": "claude-3-5-sonnet-20241022",
            "retrieval_alpha": 0.5,
            "retriever_top_k": 3,
            "multi_query_retriever": False,
        }
        
        doc_args = {
            "repo_id": project.docs_repo_id,
            "embedding_provider": "openai",
            "embedding_model": "text-embedding-3-large",
            "vector_store_provider": "pinecone",
            "index_namespace": "doc"+sanitize_repo_url(project.docs_repo_id),
            "index_name": "docembeddings",
            "retrieval_alpha": 0.5,
            "retriever_top_k": 5,
            "multi_query_retriever": False,
        }

        # Build the documentation update chain
        update_chain = build_documentation_update_chain(code_args, doc_args)
        print("update_chain: ", update_chain)
        # Get recent changes from the code repository
        code_changes = project.diffs # You'll need to implement this to get recent git changes
        print("code_changes: ", code_changes)
        # Process the changes and get documentation update suggestions
        update_suggestions = await update_chain(code_changes)

        changes = extract_documentation_changes(update_suggestions)
        print("changes: ", changes)

        # repo_manager = GitHubRepoManager(repo_id=project.docs_repo_id, access_token="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")
        # repo_manager.create_documentation_pr(changes)

        # create a new pr using update_docs endpoint
        update_docs_response = await update_docs(DocumentationUpdate(docs_repo_id=project.docs_repo_id, changes=changes))
        print("update_docs_response: ", update_docs_response)
        
        return {"suggestions": changes}
        
    except Exception as e:
        print(f"Error in get_recent_changes: {str(e)}")  # Add logging
        raise HTTPException(status_code=500, detail=str(e))

# update the documentation
@router.post("/update_docs")
async def update_docs(project: DocumentationUpdate):
    try:
        print("update_docs: project: ", project)
        print("update_docs: changes: ", project.changes)
        base_dir = os.path.join(os.getcwd(), "extractedRepos")
        
        # Create repo-specific directory
        repo_name = project.docs_repo_id.split('/')[0]  # Get 'shadcn-ui' from 'shadcn-ui/ui'
        repo_dir = os.path.join(base_dir, repo_name.replace('-', '_'))  # shadcn_ui
        local_dir = os.path.join(repo_dir, project.docs_repo_id.split('/')[1] + "documentation")
        repo_manager = GitHubRepoManager(repo_id=project.docs_repo_id, local_dir=local_dir, access_token="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")
        repo_manager.create_documentation_pr(project.changes)
        return {"message": "Documentation updated successfully"}
    except Exception as e:
        print(e)
        raise HTTPException(status_code=400, detail=str(e))

