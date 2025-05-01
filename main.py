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
        # 初次请求，获取验证码页面
        r = await client.get(SEARCH_API + wd, headers=headers)
        if "/WAF/VERIFY/CAPTCHA" in r.text:
            soup = BeautifulSoup(r.text, "html.parser")
            captcha_path = soup.find("a")["href"]
            verify_url = BASE_URL + captcha_path

            # 获取验证码图片页面
            r2 = await client.get(verify_url, headers=headers)
            soup2 = BeautifulSoup(r2.text, "html.parser")
            img_tag = soup2.find("img")
            if not img_tag:
                return {"status": "fail", "reason": "未找到验证码图片"}
            img_url = BASE_URL + img_tag["src"]

            # 下载验证码图片
            r3 = await client.get(img_url, headers=headers)
            image = Image.open(io.BytesIO(r3.content)).convert("L")
            captcha_code = pytesseract.image_to_string(image).strip()
            captcha_code = re.sub(r"\W", "", captcha_code)[:6]  # 简单清洗

            # 提交验证码
            form_action = soup2.find("form")["action"]
            token_input = soup2.find("input", {"name": "token"})
            if not token_input:
                return {"status": "fail", "reason": "未找到token"}
            token = token_input["value"]

            form_data = {
                "token": token,
                "captcha": captcha_code
            }
            submit_url = BASE_URL + form_action
            await client.post(submit_url, data=form_data, headers=headers)

            # 再次访问原始接口
            r5 = await client.get(SEARCH_API + wd, headers=headers)
            return {"status": "ok", "xml": r5.text}

        else:
            return {"status": "ok", "xml": r.text}


@app.post("/ocr")
async def ocr_api(file: UploadFile):
    content = await file.read()
    image = Image.open(io.BytesIO(content)).convert("L")
    text = pytesseract.image_to_string(image)
    return {"text": text.strip()}