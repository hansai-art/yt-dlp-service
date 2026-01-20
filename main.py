from fastapi import FastAPI, HTTPException  
from fastapi.middleware.cors import CORSMiddleware  
from fastapi.staticfiles import StaticFiles  
from fastapi.responses import FileResponse  
from pydantic import BaseModel  
import requests  
import os  
from pathlib import Path  
app = FastAPI()  
# 加入 CORS middleware - 允許所有網域  
app.add_middleware(  
    CORSMiddleware,  
    allow_origins=["*"],  
    allow_credentials=False,  
    allow_methods=["*"],  
    allow_headers=["*"],  
)  
# Cobalt API 設置  
COBALT_API_URL = "https://api.cobalt.tools/api/v1/media"  
class DownloadRequest(BaseModel):  
    url: str  
@app.get("/")  
async def root():  
    """返回前端頁面"""  
    return FileResponse("index.html", media_type="text/html")  
@app.post("/api/download")  
async def download(req: DownloadRequest):  
    """  
    使用 Cobalt API 下載影片  
    2026年仍然可用的穩定方案  
    """  
    try:  
        url = req.url.strip()  
          
        if not url:  
            raise HTTPException(status_code=400, detail="請輸入有效的URL")  
          
        # 調用 Cobalt API  
        payload = {  
            "url": url,  
            "downloadMode": "auto",  
            "filenamePattern": "basic"  
        }  
          
        headers = {  
            "Accept": "application/json",  
            "Content-Type": "application/json"  
        }  
          
        response = requests.post(  
            COBALT_API_URL,  
            json=payload,  
            headers=headers,  
            timeout=30  
        )  
          
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
                raise HTTPException(  
                    status_code=400,  
                    detail="無法取得下載鏈接"  
                )  
        else:  
            raise HTTPException(  
                status_code=response.status_code,  
                detail=f"API錯誤: {response.status_code}"  
            )  
              
    except requests.Timeout:  
        raise HTTPException(  
            status_code=408,  
            detail="請求超時，請稍後重試"  
        )  
    except requests.RequestException as e:  
        raise HTTPException(  
            status_code=500,  
            detail=f"網路錯誤: {str(e)}"  
        )  
    except Exception as e:  
        raise HTTPException(  
            status_code=500,  
            detail=f"發生錯誤: {str(e)}"  
        )  
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
