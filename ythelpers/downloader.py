import asyncio
import os

import yt_dlp
from sqlalchemy.orm import Session

from app.auth.database import SessionLocal
from app.models import Song, DownloadHistory

BASE_DIR = "/opt/muzic"
DOWNLOAD_DIR = os.path.join(BASE_DIR, "downloads")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)


def download_playlist(
    url: str,
    job_id: str,
    manager,
    loop,
    user_id: int,
):

    db: Session = SessionLocal()

    try:

        # Read playlist/video info
        with yt_dlp.YoutubeDL({"quiet": True}) as ydl:
            playlist_info = ydl.extract_info(url, download=False)

        if playlist_info.get("_type") == "playlist":
            playlist_id = playlist_info.get("id")
            playlist_title = playlist_info.get("title")
            entries = playlist_info.get("entries", [])
        else:
            playlist_id = None
            playlist_title = None
            entries = [playlist_info]

        # ---------------------------------------
        # Skip songs already downloaded
        # ---------------------------------------

        download_urls = []

        for entry in entries:

            if not entry:
                continue

            video_id = entry.get("id")

            if not video_id:
                continue

            mp3_path = os.path.join(
                DOWNLOAD_DIR,
                f"{video_id}.mp3",
            )

            song = (
                db.query(Song)
                .filter(Song.youtube_id == video_id)
                .first()
            )

            if song and os.path.exists(mp3_path):
                print(f"Skipping {video_id}")
                continue

            download_urls.append(
                f"https://www.youtube.com/watch?v={video_id}"
            )

        total_videos = len(download_urls)

        if total_videos == 0:

            send_data = {
                "status": "completed",
                "current": 0,
                "total": 0,
                "overall_percent": 100,
                "message": "All songs already downloaded",
            }

            future = asyncio.run_coroutine_threadsafe(
                manager.send(job_id, send_data),
                loop,
            )

            future.result(timeout=5)
            return

        playlist = {
            "current": 0,
            "total": total_videos,
            "last_video": None,
        }

        progress = {
            "last_percent": -1,
        }

        def send(data):
            try:
                future = asyncio.run_coroutine_threadsafe(
                    manager.send(job_id, data),
                    loop,
                )
                future.result(timeout=5)

            except Exception as e:
                print("Send error:", e)

        def progress_hook(d):

            info = d.get("info_dict", {})

            title = info.get("title", "")
            video_id = info.get("id", "")

            if video_id and video_id != playlist["last_video"]:
                playlist["last_video"] = video_id
                playlist["current"] += 1
                progress["last_percent"] = -1

            current = playlist["current"] or 1
            total = playlist["total"]

            if d["status"] == "downloading":

                total_bytes = (
                    d.get("total_bytes")
                    or d.get("total_bytes_estimate")
                    or 0
                )

                if not total_bytes:
                    return

                downloaded = d.get("downloaded_bytes", 0)

                percent = int(downloaded * 100 / total_bytes)

                if percent == progress["last_percent"]:
                    return

                progress["last_percent"] = percent

                overall = round(
                    ((current - 1) + percent / 100)
                    / total
                    * 100,
                    2,
                )

                send({
                    "status": "downloading",
                    "video_id": video_id,
                    "title": title,
                    "current": current,
                    "total": total,
                    "file_percent": percent,
                    "overall_percent": overall,
                    "speed": d.get("speed"),
                    "eta": d.get("eta"),
                })

            elif d["status"] == "finished":

                try:

                    filename = f"{video_id}.mp3"

                    song = (
                        db.query(Song)
                        .filter(Song.youtube_id == video_id)
                        .first()
                    )

                    if not song:

                        song = Song(
                            youtube_id=video_id,
                            filename=title,
                        )

                        db.add(song)

                    history = DownloadHistory(
                        user_id=user_id,
                        youtube_id=video_id,
                        youtube_playlist_id=playlist_id,
                        playlist_title=playlist_title,
                    )

                    db.add(history)
                    db.commit()

                except Exception as e:

                    db.rollback()
                    print("Database error:", e)

                send({
                    "status": "converting",
                    "video_id": video_id,
                    "title": title,
                    "current": current,
                    "total": total,
                    "overall_percent": round(
                        current / total * 100,
                        2,
                    ),
                })

        ydl_opts = {
            "format": "bestaudio/best",

            "outtmpl": os.path.join(
                DOWNLOAD_DIR,
                "%(id)s.%(ext)s",
            ),

            "writethumbnail": True,
            "ignoreerrors": True,
            "keepvideo": False,

            "progress_hooks": [progress_hook],

            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                },
                {
                    "key": "FFmpegThumbnailsConvertor",
                    "format": "jpg",
                },
            ],

            "writeinfojson": False,
            "writesubtitles": False,
            "writeautomaticsub": False,
            "writedescription": False,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download(download_urls)

        send({
            "status": "completed",
            "current": total_videos,
            "total": total_videos,
            "overall_percent": 100,
        })

    except Exception as e:

        send({
            "status": "error",
            "message": str(e),
        })

    finally:
        db.close()