import os
from app.auth.dependencies import get_current_user
from app.models import User
from app.models import Song,DownloadHistory
from app.auth.database import get_db,SessionLocal
from sqlalchemy.orm import Session
import asyncio
import uuid
import yt_dlp
from fastapi import FastAPI, APIRouter, Depends, HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect, status
from fastapi.middleware.cors import CORSMiddleware
from app.ythelpers.downloader import download_playlist
from app.ythelpers.manager import manager
from app.schemas.playlist import PlaylistRequest
from app.models import DownloadHistory



router = APIRouter(
    prefix="/yt",
    tags=["Youtube"],
)


    
        
@router.get("/playlist-info")
def playlist_info(
    video_url:str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    ):

    opts = {
        "extract_flat":True,
        "quiet":True
    }

    with yt_dlp.YoutubeDL(opts) as ydl:

        info = ydl.extract_info(video_url,download=False)

    entries = info.get("entries",[])
    
 

    return {
        "title":info["title"],
        "count":len(entries),
        "thumbnail":info.get("thumbnail"),
        "videos":[
            {
                "title":e["title"],
                "thumbnail":e.get("thumbnails",[{}])[-1].get("url")
            }
            for e in entries
        ]
    }


@router.post("/download")
async def download(
    req: PlaylistRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),    
    ):

    job_id = str(uuid.uuid4())

    loop = asyncio.get_running_loop()

    background_tasks.add_task(
        download_playlist,
        req.video_url,
        job_id,
        manager,
        loop,
        current_user.id,
    )

    return {"job_id": job_id}


@router.websocket("/ws/{job_id}")
async def websocket(websocket: WebSocket, job_id: str):
    await manager.connect(job_id, websocket)

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(job_id)
        
        
        """ 
@router.websocket("/ws/{job_id}")
async def websocket(
    websocket: WebSocket,
    job_id: str,
):
    token = websocket.query_params.get("token")

    if not token:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    try:
        current_user = await get_current_user_ws(token)
    except Exception:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await manager.connect(job_id, websocket)

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(job_id) """