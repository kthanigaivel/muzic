from fastapi import FastAPI,Request

from app.auth.database import Base, engine
from fastapi.middleware.cors import CORSMiddleware

# Import models so SQLAlchemy registers them
import app.models.user

# Import API routers
from app.routers.auth import router as auth_router
from app.routers.yt_dlp import router as import_router
from app.routers.songs import  router as songs_router
from app.routers.user import router as user_router
from app.routers.favorite import router as fav_router
from app.routers.dashboard import router as dash_router
from app.routers.clean import router as clean_router


from fastapi.templating import Jinja2Templates


app = FastAPI(
    title="Muzic API",
    version="1.0.0",
    description="Music Streaming API by thanigai",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins (change to your frontend URL in production)
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods (GET, POST, OPTIONS, etc.)
    allow_headers=["*"],  # Allows all headers
)

# Create tables (temporary until Alembic is configured)
Base.metadata.create_all(bind=engine)

# Register routers
app.include_router(auth_router)
app.include_router(import_router)
app.include_router(songs_router)
app.include_router(user_router)
app.include_router(fav_router)
app.include_router(dash_router)
app.include_router(clean_router)



templates = Jinja2Templates(directory="/opt/muzic/app/templates")

@app.get("/")
def index(request: Request):
    return templates.TemplateResponse(
        request,
        "index.html",
        {}
    )
    

@app.get("/dash")
def index(request: Request):
    return templates.TemplateResponse(
        request,
        "dashboard.html",
        {}
    )
