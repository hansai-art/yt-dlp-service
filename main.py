from fastapi import FastAPI
from pydantic import BaseModel
import subprocess
import json
import tempfile

app = FastAPI()

class Req(BaseModel):
    url: str

@app.post("/extract")
async def extract(req: Req):

    try:
        # 使用暫存檔來接 yt-dlp 回傳的 JSON
        with tempfile.NamedTemporaryFile(delete=True) as tmp:
            cmd = [
                "yt-dlp",
                "--no-warnings",
                "--dump-json",
                req.url
            ]

            # 執行 yt-dlp
            result = subprocess.run(
                cmd,
                stdout=tmp,
                stderr=subprocess.PIPE,
                text=True
            )

            # 如果 yt-dlp 回傳錯誤（例如 YouTube 限制）
            if result.returncode != 0:
                return {
                    "success": False,
                    "error": "yt-dlp-error",
                    "stderr": result.stderr[:500]  # 截前 500 字避免太長
                }

            # 成功 → 讀取 JSON 內容
            tmp.seek(0)
            data = json.load(tmp)

            # yt-dlp JSON 裡應該有 direct URL
            if "url" not in data:
                return {
                    "success": False,
                    "error": "no_url_in_json",
                    "raw": str(data)[:300]
                }

            return {
                "success": True,
                "url": data["url"],
                "title": data.get("title"),
                "duration": data.get("duration"),
            }

    except Exception as e:
        return {
            "success": False,
            "error": "exception",
            "message": str(e)
        }
