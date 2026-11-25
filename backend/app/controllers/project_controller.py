from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from typing import List

from backend.app.core.database import get_db
from backend.app.core.dependencies import get_current_user
from backend.app.schemas.project import ProjectCreate, ProjectRead
from backend.app.services.project_service import ProjectService
from backend.app.models.user import User

router = APIRouter(prefix="/api/projects", tags=["Projects"])

@router.post("", response_model=ProjectRead, status_code=201)
def create_project(
    project_in: ProjectCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new DOST-funded research project profile.
    Protected endpoint: requires an authenticated active user.
    """
    client_ip = request.client.host if request.client else None
    return ProjectService.create_project(
        db=db,
        project_in=project_in,
        acting_user=current_user,
        client_ip=client_ip
    )

@router.get("", response_model=List[ProjectRead])
def list_projects(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all registered projects. Protected endpoint: requires authenticated active user."""
    return ProjectService.list_projects(db, skip=skip, limit=limit)

@router.get("/{project_id}", response_model=ProjectRead)
def get_project(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieve details of a specific project by ID."""
    return ProjectService.get_project(db, project_id=project_id)
