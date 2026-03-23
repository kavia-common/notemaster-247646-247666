from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.core.settings import get_settings
from src.api.routers import auth, notes, search, tags

settings = get_settings()

openapi_tags = [
    {"name": "auth", "description": "Registration, login (JWT), and current-user endpoints."},
    {"name": "notes", "description": "Notes CRUD, pin/unpin, favorite/unfavorite, and note-tag assignment."},
    {"name": "tags", "description": "Tags CRUD and listing."},
    {"name": "search", "description": "Search endpoints for notes."},
]

app = FastAPI(
    title="NoteMaster Backend API",
    description="FastAPI backend for a full-stack notes application with JWT auth, tagging, favorites, pinning, and search.",
    version="1.0.0",
    openapi_tags=openapi_tags,
)

# CORS must allow the Next.js frontend origin(s). Configure via CORS_ALLOW_ORIGINS env var.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(notes.router)
app.include_router(tags.router)
app.include_router(search.router)


@app.get(
    "/",
    tags=["auth"],
    summary="Health check",
    description="Basic health-check endpoint.",
)
def health_check():
    """Health check endpoint used by deployments and monitoring."""
    return {"message": "Healthy"}
