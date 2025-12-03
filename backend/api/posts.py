from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import desc

from database import get_db
from models import User, Post
from schemas import PostCreate, PostResponse, PostDetailResponse, UserProfileResponse
from dependencies import get_current_user

router = APIRouter(prefix="/api/posts", tags=["posts"])


@router.post("", response_model=PostResponse)
def create_post(
    post_data: PostCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    new_post = Post(
        user_id=current_user.id,
        title=post_data.title,
        content=post_data.content,
    )

    db.add(new_post)
    db.commit()
    db.refresh(new_post)

    return PostResponse.model_validate(new_post)


@router.get("", response_model=list[PostDetailResponse])
def list_posts(
    db: Session = Depends(get_db),
):
    posts = db.query(Post).order_by(desc(Post.created_at)).all()
    return [PostDetailResponse.model_validate(post) for post in posts]


@router.get("/my", response_model=list[PostResponse])
def get_my_posts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    posts = db.query(Post).filter(Post.user_id == current_user.id).order_by(desc(Post.created_at)).all()
    return [PostResponse.model_validate(post) for post in posts]


@router.get("/user/{user_id}", response_model=list[PostResponse])
def get_user_posts(
    user_id: int,
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    posts = db.query(Post).filter(Post.user_id == user_id).order_by(desc(Post.created_at)).all()
    return [PostResponse.model_validate(post) for post in posts]


@router.get("/{post_id}", response_model=PostDetailResponse)
def get_post(post_id: int, db: Session = Depends(get_db)):
    post = db.query(Post).filter(Post.id == post_id).first()

    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found",
        )

    return PostDetailResponse.model_validate(post)


@router.delete("/{post_id}")
def delete_post(
    post_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    post = db.query(Post).filter(Post.id == post_id).first()

    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found",
        )

    if post.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Can only delete your own posts",
        )

    db.delete(post)
    db.commit()

    return {"message": "Post deleted successfully"}
