from fastapi import FastAPI
from pydantic import BaseModel
import yt_dlp

app = FastAPI()

class Req(BaseModel):
    url: str
    quality: str = "best[height<=720]"

@app.post("/extract")
def extract(r: Req):
    ydl_opts = {
        "quiet": True,
        "skip_download": True,
        "format": r.quality,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(r.url, download=False)
        return {
            "url": info["url"],
            "filename": info.get("title", "video") + ".mp4"
        }
