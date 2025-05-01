from fastapi import FastAPI, UploadFile, Form
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import httpx
from bs4 import BeautifulSoup
import pytesseract
from PIL import Image
import io
import re

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
}

BASE_URL = "http://cj.ffzyapi.com"
SEARCH_API = f"{BASE_URL}/api.php/provide/vod/at/xml/?wd="

@app.get("/search")
async def search(wd: str):
    async with httpx.AsyncClient(follow_redirects=True) as client:
        r = await client.get(SEARCH_API + wd, headers=headers)

        # 检查是否进入验证码重定向页面
        if "/WAF/VERIFY/CAPTCHA" in r.text:
            soup = BeautifulSoup(r.text, "html.parser")
            img_tag = soup.find("img", id="ui-captcha-image")
            if not img_tag:
                return {"status": "fail", "reason": "未找到验证码图片"}

            img_src = img_tag.get("src")
            img_url = BASE_URL + img_src

            # 下载验证码图片
            img_response = await client.get(img_url, headers=headers)
            image = Image.open(io.BytesIO(img_response.content)).convert("L")
            captcha_code = pytesseract.image_to_string(image).strip()
            captcha_code = re.sub(r"\W", "", captcha_code)[:6]  # 简单清洗

            # 获取 CAPTCHA ID
            captcha_id_input = soup.find("input", {"name": "GOEDGE_WAF_CAPTCHA_ID"})
            if not captcha_id_input:
                return {"status": "fail", "reason": "未找到验证码 ID"}
            captcha_id = captcha_id_input["value"]

            # 提交验证码
            post_url = BASE_URL + "/WAF/VERIFY/CAPTCHA"
            form_data = {
                "GOEDGE_WAF_CAPTCHA_ID": captcha_id,
                "GOEDGE_WAF_CAPTCHA_CODE": captcha_code
            }

            await client.post(post_url, data=form_data, headers=headers)

            # 再次访问原始接口
            r2 = await client.get(SEARCH_API + wd, headers=headers)
            return {"status": "ok", "captcha_code": captcha_code, "xml": r2.text}

        return {"status": "ok", "xml": r.text}

@app.post("/ocr")
async def ocr_api(file: UploadFile):
    content = await file.read()
    image = Image.open(io.BytesIO(content)).convert("L")
    text = pytesseract.image_to_string(image)
    return {"text": text.strip()}
