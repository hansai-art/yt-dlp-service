from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
import httpx
from pathlib import Path
from urllib.parse import urlparse

app = FastAPI()

# 適用 Zeabur 的 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Cobalt 2026 最新 API
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
    steps = []  # 用來回報每一步狀態

    try:
        # ===== Step 1: 驗證 URL =====
        steps.append("Step 1: validating URL…")
        url = req.url.strip()
        parsed = urlparse(url)
        if not parsed.scheme.startswith("http"):
            raise HTTPException(400, "無效連結（URL 格式錯誤）")

        # ===== Step 2: 準備 payload =====
        steps.append("Step 2: preparing request payload…")
        payload = {
            "url": url,
            "vCodec": "h264",
            "vQuality": "1080",
            "aFormat": "mp3",
            "filenamePattern": "basic"
        }

        # ===== Step 3: 發送 API 請求 =====
        steps.append("Step 3: sending request to Cobalt API…")

        async with httpx.AsyncClient(
            timeout=30,
            follow_redirects=True
        ) as client:
            response = await client.post(COBALT_API_URL, json=payload)

        # ===== Step 4: 已收到 Cobalt 回應 =====
        steps.append(f"Step 4: received response from Cobalt (HTTP {response.status_code})")

        # ===== Step 5: 嘗試解析 JSON =====
        steps.append("Step 5: parsing JSON response…")

        try:
            data = response.json()
        except Exception:
            raise HTTPException(
                500,
                detail={
                    "message": "Cobalt 回傳非 JSON（可能被 Cloudflare human-check 擋下）",
                    "steps": steps,
                    "rawText": response.text[:500]
                }
            )

        # ===== Step 6: 檢查 Cobalt 的結果 =====
        if data.get("status") == "ok" and data.get("url"):
            steps.append("Step 6: Cobalt returned valid download info.")
            return {
                "success": True,
                "downloadUrl": data["url"],
                "filename": data.get("filename", "video"),
                "title": data.get("title", ""),
                "steps": steps,
                "rawResponse": data
            }

        # ===== Step 6b: Cobalt 回傳錯誤 =====
        steps.append("Step 6: Cobalt returned an error message.")
        raise HTTPException(
            400,
            detail={
                "message": data.get("error", "Cobalt 未提供可用下載連結"),
                "steps": steps,
                "rawResponse": data
            }
        )

    except HTTPException as e:
        # e.detail 可以是字串或 dict，全部包進回傳
        raise HTTPException(
            e.status_code,
            detail={
                "message": e.detail,
                "steps": steps
            }
        )
    except httpx.TimeoutException:
        steps.append("Timeout: Cobalt API 未在 30 秒內回應")
        raise HTTPException(408, {"message": "Cobalt API 請求超時", "steps": steps})
    except Exception as e:
        steps.append("Unexpected backend error.")
        raise HTTPException(
            500,
            detail={
                "message": str(e),
                "steps": steps
            }
        )


@app.get("/api/health")
async def health():
    return {
        "status": "healthy",
        "api": "cobalt-2026",
        "environment": "zeabur-compatible"
    }
