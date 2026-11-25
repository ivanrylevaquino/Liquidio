from sqlalchemy.orm import Session
from sqlalchemy import select
from typing import List
from backend.app.models.project import Project

class ProjectRepository:
    """
    Data access repository for Project entities.
    Encapsulates all database operations for projects.
    """
    @staticmethod
    def get_by_id(db: Session, project_id: int) -> Project | None:
        return db.get(Project, project_id)

    @staticmethod
    def get_by_code(db: Session, project_code: str) -> Project | None:
        stmt = select(Project).where(Project.project_code == project_code)
        return db.execute(stmt).scalar_one_or_none()

    @staticmethod
    def create(db: Session, project: Project) -> Project:
        db.add(project)
        db.commit()
        db.refresh(project)
        return project

    @staticmethod
    def get_all(db: Session, skip: int = 0, limit: int = 100) -> List[Project]:
        stmt = select(Project).order_by(Project.id).offset(skip).limit(limit)
        return list(db.execute(stmt).scalars().all())
