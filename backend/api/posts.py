import os
import uuid
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional

from database import get_db
from models import User, Post, PostMedia
from schemas import PostCreate, PostResponse, PostDetailResponse, PostMediaResponse
from dependencies import get_current_user

router = APIRouter(prefix="/api/posts", tags=["posts"])

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

ALLOWED_EXTENSIONS = {
    'image': ['jpg', 'jpeg', 'png', 'gif', 'webp'],
    'audio': ['mp3', 'wav', 'ogg', 'm4a'],
    'video': ['mp4', 'webm', 'mov', 'avi'],
    'pdf': ['pdf']
}

ALLOWED_MIME_TYPES = {
    'image/jpeg': 'image',
    'image/png': 'image',
    'image/gif': 'image',
    'image/webp': 'image',
    'audio/mpeg': 'audio',
    'audio/mp3': 'audio',
    'audio/wav': 'audio',
    'audio/ogg': 'audio',
    'audio/m4a': 'audio',
    'audio/x-m4a': 'audio',
    'video/mp4': 'video',
    'video/webm': 'video',
    'video/quicktime': 'video',
    'video/x-msvideo': 'video',
    'application/pdf': 'pdf'
}

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB


def get_media_type(content_type: str, filename: str) -> Optional[str]:
    if content_type in ALLOWED_MIME_TYPES:
        return ALLOWED_MIME_TYPES[content_type]
    
    ext = filename.lower().split('.')[-1] if '.' in filename else ''
    for media_type, extensions in ALLOWED_EXTENSIONS.items():
        if ext in extensions:
            return media_type
    return None


async def get_file_size(file: UploadFile) -> int:
    file.file.seek(0, 2)
    size = file.file.tell()
    file.file.seek(0)
    return size


@router.post("", response_model=PostResponse)
async def create_post(
    title: str = Form(...),
    content: str = Form(...),
    files: List[UploadFile] = File(default=[]),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    new_post = Post(
        user_id=current_user.id,
        title=title,
        content=content,
    )

    db.add(new_post)
    db.commit()
    db.refresh(new_post)

    for file in files:
        if not file.filename:
            continue
            
        file_size = await get_file_size(file)
        if file_size == 0:
            continue
            
        media_type = get_media_type(file.content_type or '', file.filename)
        if not media_type:
            continue
        
        if file_size > MAX_FILE_SIZE:
            continue

        ext = file.filename.split('.')[-1] if '.' in file.filename else ''
        unique_filename = f"{uuid.uuid4().hex}.{ext}"
        file_path = os.path.join(UPLOAD_DIR, unique_filename)

        file_content = await file.read()
        with open(file_path, "wb") as buffer:
            buffer.write(file_content)

        post_media = PostMedia(
            post_id=new_post.id,
            filename=unique_filename,
            original_filename=file.filename,
            file_path=f"/api/uploads/{unique_filename}",
            media_type=media_type,
            mime_type=file.content_type or 'application/octet-stream',
            file_size=file_size,
        )
        db.add(post_media)

    db.commit()
    db.refresh(new_post)

    return PostResponse.model_validate(new_post)


@router.post("/{post_id}/media", response_model=PostMediaResponse)
async def add_media_to_post(
    post_id: int,
    file: UploadFile = File(...),
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
            detail="Can only add media to your own posts",
        )

    media_type = get_media_type(file.content_type or '', file.filename or '')
    if not media_type:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File type not allowed. Allowed types: images, audio, video, PDF",
        )
    
    file_size = await get_file_size(file)
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too large. Maximum size is {MAX_FILE_SIZE // (1024*1024)}MB",
        )

    ext = file.filename.split('.')[-1] if file.filename and '.' in file.filename else ''
    unique_filename = f"{uuid.uuid4().hex}.{ext}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)

    file_content = await file.read()
    with open(file_path, "wb") as buffer:
        buffer.write(file_content)

    post_media = PostMedia(
        post_id=post_id,
        filename=unique_filename,
        original_filename=file.filename or 'unknown',
        file_path=f"/api/uploads/{unique_filename}",
        media_type=media_type,
        mime_type=file.content_type or 'application/octet-stream',
        file_size=file_size,
    )
    db.add(post_media)
    db.commit()
    db.refresh(post_media)

    return PostMediaResponse.model_validate(post_media)


@router.delete("/media/{media_id}")
def delete_media(
    media_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    media = db.query(PostMedia).filter(PostMedia.id == media_id).first()
    if not media:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Media not found",
        )
    
    post = db.query(Post).filter(Post.id == media.post_id).first()
    if not post or post.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Can only delete media from your own posts",
        )

    file_path = os.path.join(UPLOAD_DIR, media.filename)
    if os.path.exists(file_path):
        os.remove(file_path)

    db.delete(media)
    db.commit()

    return {"message": "Media deleted successfully"}


@router.get("", response_model=list[PostDetailResponse])
def list_posts(db: Session = Depends(get_db)):
    posts = db.query(Post).order_by(desc(Post.created_at)).all()
    return [PostDetailResponse.model_validate(post) for post in posts]


@router.get("/my", response_model=list[PostResponse])
def get_my_posts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    posts = db.query(Post).filter(Post.user_id == current_user.id).order_by(
        desc(Post.created_at)).all()
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

    posts = db.query(Post).filter(Post.user_id == user_id).order_by(
        desc(Post.created_at)).all()
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

    for media in post.media:
        file_path = os.path.join(UPLOAD_DIR, media.filename)
        if os.path.exists(file_path):
            os.remove(file_path)

    db.delete(post)
    db.commit()

    return {"message": "Post deleted successfully"}
