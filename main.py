from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import httpx
from pathlib import Path
from urllib.parse import urlparse
import logging

logger = logging.getLogger("uvicorn.error")

app = FastAPI()

# 加入 CORS middleware - 允許所有網域（注意安全性）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 若你有 static 資源，可以 mount 靜態目錄 (可選)
# app.mount("/static", StaticFiles(directory=Path(__file__).parent / "static"), name="static")

COBALT_API_URL = "https://api.cobalt.tools/api/v1/media"

class DownloadRequest(BaseModel):
    url: str

INDEX_PATH = Path(__file__).parent / "index.html"

@app.get("/")
async def root():
    """返回前端頁面"""
    if not INDEX_PATH.exists():
        raise HTTPException(status_code=404, detail="index.html not found")
    return FileResponse(INDEX_PATH, media_type="text/html")

@app.post("/api/download")
async def download(req: DownloadRequest):
    """
    使用 Cobalt API 下載影片（改用非阻塞 httpx）
    """
    url = (req.url or "").strip()
    if not url:
        raise HTTPException(status_code=400, detail="請輸入有效的URL")

    # 基本 URL 驗證（可依需求加強）
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        raise HTTPException(status_code=400, detail="不支援的URL")

    payload = {
        "url": url,
        "downloadMode": "auto",
        "filenamePattern": "basic"
    }

    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(COBALT_API_URL, json=payload, headers=headers)

        if response.status_code == 200:
            result = response.json()
            if result.get("url"):
                return {
                    "success": True,
                    "downloadUrl": result.get("url"),
                    "filename": result.get("filename", "影片"),
                    "title": result.get("title", "下載中..."),
                    "source": "cobalt"
                }
            else:
                raise HTTPException(status_code=400, detail="無法取得下載鏈接")
        else:
            # 將第三方 API 錯誤回傳給客戶端
            raise HTTPException(status_code=response.status_code, detail=f"API錯誤: {response.status_code}")

    except HTTPException:
        # 不要吞掉已經準備要回傳的 HTTPException
        raise
    except httpx.TimeoutException:
        raise HTTPException(status_code=408, detail="請求超時，請稍後重試")
    except httpx.RequestError as e:
        logger.exception("網路錯誤")
        raise HTTPException(status_code=502, detail=f"網路錯誤: {str(e)}")
    except Exception as e:
        logger.exception("未處理的錯誤")
        raise HTTPException(status_code=500, detail=f"發生錯誤: {str(e)}")

@app.get("/api/health")
async def health():
    """健康檢查"""
    return {"status": "healthy", "api": "cobalt"}

@app.get("/api/supported-platforms")
async def supported_platforms():
    """返回支援的平台列表"""
    return {
        "platforms": [
            "YouTube",
            "TikTok",
            "Instagram",
            "Twitter/X",
            "Reddit",
            "Pinterest",
            "Tumblr",
            "Vimeo",
            "Dailymotion",
            "Bilibili"
        ],
        "note": "Cobalt API 支援多個平台，2026年仍然可用"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)