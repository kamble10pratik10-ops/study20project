from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc
from database import get_db
from models import Project, User
from schemas import ProjectCreate, ProjectResponse, ProjectDetailResponse
from dependencies import get_current_user

router = APIRouter(prefix="/api/projects", tags=["projects"])


@router.post("/create", response_model=ProjectResponse)
def create_project(
    project_data: ProjectCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new project"""
    new_project = Project(
        title=project_data.title,
        description=project_data.description,
        github_url=project_data.github_url,
        demo_url=project_data.demo_url,
        technologies=project_data.technologies,
        created_by=current_user.id,
    )

    db.add(new_project)
    db.commit()
    db.refresh(new_project)

    # Reload with relationship
    project = (
        db.query(Project)
        .options(joinedload(Project.created_by_user))
        .filter(Project.id == new_project.id)
        .first()
    )

    return ProjectResponse.model_validate(project)


@router.get("/list", response_model=list[ProjectResponse])
def list_projects(db: Session = Depends(get_db)):
    """Get all projects (no authentication required)"""
    print("list_projects")
    projects = (
        db.query(Project)
        .options(joinedload(Project.created_by_user))
        .order_by(desc(Project.created_at))
        .all()
    )
    return [ProjectResponse.model_validate(project) for project in projects]

@router.get("/{project_id}", response_model=ProjectDetailResponse)
def get_project(project_id: int, db: Session = Depends(get_db)):
    """Get a specific project by ID (no authentication required)"""
    project = (
        db.query(Project)
        .options(joinedload(Project.created_by_user))
        .filter(Project.id == project_id)
        .first()
    )
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    return ProjectDetailResponse.model_validate(project)
