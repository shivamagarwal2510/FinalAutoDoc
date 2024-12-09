from fastapi import APIRouter, HTTPException
from backend.app.models.schemas import ProjectSetup, DocumentationUpdate


router = APIRouter()

@router.post("/setup")
async def setup_project(project: ProjectSetup):
    """Initialize project repositories and setup monitoring"""
    try:
        print('project: ', project)
        
        return {"message": "Project setup successful"}
    except Exception as e:
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