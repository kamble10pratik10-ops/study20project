from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import engine, Base, SessionLocal
from config import get_settings
from models import User
from auth import get_password_hash   # keep only if needed for default user

settings = get_settings()

# Create all tables
Base.metadata.create_all(bind=engine)


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


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    create_default_user()
    yield
    # Shutdown (if needed)


app = FastAPI(
    title="LearnConnect API",
    description="A collaborative learning platform API",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Include routers
from api import auth, groups, dashboard, doubts, search

app.include_router(auth.router)
app.include_router(groups.router)
app.include_router(dashboard.router)
app.include_router(doubts.router)
app.include_router(search.router)


@app.get("/")
def health_check():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
