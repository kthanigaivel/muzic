from fastapi import APIRouter, Depends, HTTPException, status

from fastapi import FastAPI,Request

from app.auth.database import Base, engine

# Import models so SQLAlchemy registers them
import app.models.user

# Import API routers
from app.routers.auth import router as auth_router
from app.routers.yt_dlp import router as import_router
from app.routers.songs import  router as songs_router

from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="/opt/muzic/app/templates")

router = APIRouter(
    prefix="/user",
    tags=["Authentication"],
)
     

@router.get("/profile")
def index(request: Request):
    return templates.TemplateResponse(
        request,
        "profile.html",
        {}
    )
    
@router.get("/download")
def index(request: Request):
    return templates.TemplateResponse(
        request,
        "import.html",
        {}
    )
    

@router.get("/default")
def index(request: Request):
    return templates.TemplateResponse(
        request,
        "default.html",
        {}
    )
    
    
 