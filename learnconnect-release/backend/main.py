import os
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager

from database import engine, Base, SessionLocal
from config import get_settings
from models import User
from auth import get_password_hash  # Only keep if needed for default user
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import timedelta
from typing import Optional
from database import get_db
from models import User
from schemas import UserCreate, UserLogin, TokenResponse, UserResponse
from auth import get_password_hash, verify_password, create_access_token, decode_token
from config import get_settings

from sqlalchemy.orm import Session
from sqlalchemy import desc
from database import get_db
from models import User, SearchHistory, Topic
from schemas import DashboardResponse, SearchHistoryResponse, GroupResponse, TopicResponse
from dependencies import get_current_user
from api import auth, groups, search, dashboard, doubts, posts, project, users

logging.basicConfig(level=logging.INFO)

settings = get_settings()

# Create all tables (runs only once on startup)
Base.metadata.create_all(bind=engine)
logging.basicConfig(level=logging.INFO)


def create_default_user():
    """Create a default test user if it doesn't exist"""
    db = SessionLocal()
    try:
        default_email = "abc@abc.com"
        existing_user = db.query(User).filter(User.email == default_email).first()

        if not existing_user:
            default_user = User(
                name="Test User",
                email=default_email,
                password_hash=get_password_hash("abc123"),
            )
            db.add(default_user)
            db.commit()
            print(f"✓ Default user created: {default_email} / abc123")
        else:
            print(f"✓ Default user already exists: {default_email}")
    except Exception as e:
        print(f"Error creating default user: {e}")
        db.rollback()
    finally:
        db.close()


# -------------------------------
# 🚀 FIXED: Lifespan handler
# -------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 Application starting...")
    create_default_user()  # Startup logic

    yield

    print("🛑 Application shutting down...")
    # cleanup logic here (optional)


# -------------------------------
# 🚀 Correct FastAPI app instance
# -------------------------------
app = FastAPI(
    title="LearnConnect API",
    description="A collaborative learning platform API",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*", "http://localhost:8050"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(groups.router)
app.include_router(search.router)
app.include_router(dashboard.router)
app.include_router(doubts.router)
app.include_router(posts.router)
app.include_router(users.router)

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.get("/api/uploads/{filename}")
async def serve_upload(filename: str):
    file_path = os.path.join(UPLOAD_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(file_path)


# -------------------------------
# Routes
# -------------------------------
@app.get("/home")
def home():
    return {"status": "ok"}


@app.get("/")
def dev():
    return {"status": "ok"}


@app.get("/lif")
def lif():
    return {"status": "ok"}


@app.get("/health")
def health_check():
    return {"status": "health"}


# -------------------------------
# 🚀 Development server
# -------------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",  # IMPORTANT: import string (required for reload!)
        host="0.0.0.0",
        port=8058,
        reload=True)
