import asyncio
import os

import yt_dlp

BASE_DIR = "/opt/muzic"
DOWNLOAD_DIR = os.path.join(BASE_DIR, "downloads")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)


def download_playlist(url: str, job_id: str, manager, loop):

    # Get playlist info before downloading
    with yt_dlp.YoutubeDL({"quiet": True}) as ydl:
        info = ydl.extract_info(url, download=False)

    if info.get("_type") == "playlist":
        total_videos = len(info["entries"])
    else:
        total_videos = 1

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

        # New video started
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
                ((current - 1) + percent / 100) / total * 100,
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

            send({
                "status": "converting",
                "video_id": video_id,
                "title": title,
                "current": current,
                "total": total,
                "overall_percent": round(current / total * 100, 2),
            })

    ydl_opts = {
        "format": "bestaudio/best",

        # Save to downloads/youtube_id.mp3
        "outtmpl": os.path.join(DOWNLOAD_DIR, "%(id)s.%(ext)s"),

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

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

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