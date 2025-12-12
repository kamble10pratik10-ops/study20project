from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import desc
from database import get_db
from models import User, Doubt
from schemas import DoubtCreate, DoubtResponse, DoubtDetailResponse
from dependencies import get_current_user

router = APIRouter(prefix="/api/doubts", tags=["doubts"])


@router.post("/create", response_model=DoubtResponse)
def create_doubt(
    doubt_data: DoubtCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    new_doubt = Doubt(
        topic=doubt_data.topic,
        title=doubt_data.title,
        description=doubt_data.description,
        created_by=current_user.id,
    )

    db.add(new_doubt)
    db.commit()
    db.refresh(new_doubt)

    return DoubtResponse.model_validate(new_doubt)


@router.get("", response_model=list[DoubtDetailResponse])
def list_doubts(
    topic: str = None,
    db: Session = Depends(get_db),
):
    query = db.query(Doubt).order_by(desc(Doubt.created_at))

    if topic:
        query = query.filter(Doubt.topic == topic)

    doubts = query.all()

    return [DoubtDetailResponse.model_validate(doubt) for doubt in doubts]


@router.get("/{doubt_id}", response_model=DoubtDetailResponse)
def get_doubt(doubt_id: int, db: Session = Depends(get_db)):
    doubt = db.query(Doubt).filter(Doubt.id == doubt_id).first()

    if not doubt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Doubt not found",
        )

    return DoubtDetailResponse.model_validate(doubt)


@router.delete("/{doubt_id}")
def delete_doubt(
    doubt_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    doubt = db.query(Doubt).filter(Doubt.id == doubt_id).first()

    if not doubt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Doubt not found",
        )

    if doubt.created_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Can only delete your own doubts",
        )

    db.delete(doubt)
    db.commit()

    return {"message": "Doubt deleted successfully"}
