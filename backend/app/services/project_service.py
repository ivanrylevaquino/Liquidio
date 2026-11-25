from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from backend.app.models.project import Project
from backend.app.models.user import User
from backend.app.schemas.project import ProjectCreate
from backend.app.repositories.project_repository import ProjectRepository
from backend.app.repositories.activity_log_repository import ActivityLogRepository

class ProjectService:
    """
    Business logic service for Project management.
    Enforces per-project isolation and validates timeline and budget constraints.
    """
    @staticmethod
    def create_project(
        db: Session,
        project_in: ProjectCreate,
        acting_user: User,
        client_ip: str | None = None
    ) -> Project:
        # Enforce unique project_code
        existing = ProjectRepository.get_by_code(db, project_in.project_code)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Project code '{project_in.project_code}' already exists."
            )

        if project_in.end_date < project_in.start_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Project completion end_date must be on or after start_date."
            )

        new_project = Project(
            project_code=project_in.project_code,
            title=project_in.title,
            funding_agency=project_in.funding_agency,
            start_date=project_in.start_date,
            end_date=project_in.end_date,
            total_dost_budget=project_in.total_dost_budget,
            total_citu_budget=project_in.total_citu_budget
        )
        created = ProjectRepository.create(db, new_project)

        # Append-only audit log
        ActivityLogRepository.insert(
            db=db,
            action_type="PROJECT_CREATE",
            entity_name="projects",
            entity_id=created.id,
            user_id=acting_user.id,
            details={
                "project_code": created.project_code,
                "title": created.title,
                "funding_agency": created.funding_agency,
                "total_dost_budget": str(created.total_dost_budget),
                "total_citu_budget": str(created.total_citu_budget),
            },
            ip_address=client_ip
        )

        return created

    @staticmethod
    def get_project(db: Session, project_id: int) -> Project:
        project = ProjectRepository.get_by_id(db, project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project with ID {project_id} not found."
            )
        return project

    @staticmethod
    def list_projects(db: Session, skip: int = 0, limit: int = 100) -> List[Project]:
        return ProjectRepository.get_all(db, skip=skip, limit=limit)
