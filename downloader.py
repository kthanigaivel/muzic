import yt_dlp
import asyncio
import os

DOWNLOAD_DIR = "downloads"

os.makedirs(DOWNLOAD_DIR, exist_ok=True)
import os
import yt_dlp
import asyncio

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

def download_playlist(url: str, job_id: str, manager):

    progress = {
        "last_percent": -1
    }

    def send(data):
        try:
            asyncio.run(manager.send(job_id, data))
        except Exception as e:
            print(e)

    def progress_hook(d):

        info = d.get("info_dict", {})

        current = info.get("playlist_index") or 1
        total = info.get("n_entries") or 1

        title = info.get("title", "")
        video_id = info.get("id", "")

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

            # Only send when percentage changes
            if percent == progress["last_percent"]:
                return

            progress["last_percent"] = percent

            overall = round(
                ((current - 1) + percent / 100) / total * 100,
                2
            )

            send({
                "status": "downloading",
                "title": title,
                "video_id": video_id,
                "current": current,
                "total": total,
                "file_percent": percent,
                "overall_percent": overall,
                "speed": d.get("speed"),
                "eta": d.get("eta"),
            })

        elif d["status"] == "finished":

            progress["last_percent"] = -1

            send({
                "status": "converting",
                "title": title,
                "video_id": video_id,
                "current": current,
                "total": total,
                "overall_percent": round(current / total * 100, 2),
            })

    

    ydl_opts = {
        # audio only
        "format": "bestaudio/best",

        # youtube_id.mp3
        "outtmpl": "%(id)s.%(ext)s",

        # download thumbnail
        "writethumbnail": True,

        # don't stop on failed videos
        "ignoreerrors": True,

        # websocket progress
        "progress_hooks": [progress_hook],

        # convert audio + thumbnail
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

        # remove original downloaded file
        "keepvideo": False,

        # don't write extra files
        "writeinfojson": False,
        "writesubtitles": False,
        "writeautomaticsub": False,
        "writedescription": False,
    }

    try:

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        print("Download completed")

    except Exception as e:

        send({
            "status": "error",
            "message": str(e)
        })