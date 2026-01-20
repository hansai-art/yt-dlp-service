from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
import httpx
from pathlib import Path
from urllib.parse import urlparse

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 新版 Cobalt API（2026）
COBALT_API_URL = "https://api.cobalt.tools/api/json"

class DownloadRequest(BaseModel):
    url: str

INDEX_PATH = Path(__file__).parent / "index.html"


@app.get("/")
async def index():
    if not INDEX_PATH.exists():
        raise HTTPException(404, "index.html not found")
    return FileResponse(INDEX_PATH, media_type="text/html")


@app.post("/api/download")
async def download(req: DownloadRequest):
    url = req.url.strip()
    parsed = urlparse(url)
    if not parsed.scheme.startswith("http"):
        raise HTTPException(400, "無效 URL")

    payload = {
        "url": url,
        "vCodec": "h264",
        "vQuality": "1080",
        "aFormat": "mp3",
        "filenamePattern": "basic"
    }

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            res = await client.post(COBALT_API_URL, json=payload)

        if res.status_code != 200:
            raise HTTPException(res.status_code, f"Cobalt API 錯誤: {res.text}")

        data = res.json()

        # 新版 API 回傳格式
        if data.get("status") == "ok" and data.get("url"):
            return {
                "success": True,
                "downloadUrl": data["url"],
                "filename": data.get("filename", "video"),
                "title": data.get("title", ""),
                "source": "cobalt-2026"
            }

        raise HTTPException(400, data.get("error", "Cobalt 回傳無效資料"))

    except httpx.TimeoutException:
        raise HTTPException(408, "Cobalt API 超時")
    except Exception as e:
        raise HTTPException(500, f"後端錯誤: {str(e)}")


@app.get("/api/health")
async def health():
    return {"status": "healthy", "api": "cobalt-2026"}
