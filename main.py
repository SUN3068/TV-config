from fastapi import FastAPI
import httpx
from bs4 import BeautifulSoup
from pathlib import Path

app = FastAPI()

@app.get("/fetch_captcha")
async def fetch_captcha():
    base_url = "http://cj.ffzyapi.com"
    search_url = f"{base_url}/api.php/provide/vod/at/xml/?wd=流浪地球"

    async with httpx.AsyncClient(follow_redirects=True) as client:
        # 第一次请求，触发跳转到验证码页
        resp = await client.get(search_url)

        # 使用 BeautifulSoup 提取验证码图片链接
        soup = BeautifulSoup(resp.text, 'html.parser')
        img_tag = soup.find("img", id="ui-captcha-image")
        if not img_tag:
            return {"status": "fail", "message": "未找到验证码图像"}

        img_src = img_tag["src"]
        captcha_url = base_url + img_src

        # 下载验证码图片
        img_resp = await client.get(captcha_url)
        captcha_path = Path("captcha.jpg")
        captcha_path.write_bytes(img_resp.content)

        return {
            "status": "ok",
            "captcha_saved": True,
            "captcha_url": captcha_url
        }