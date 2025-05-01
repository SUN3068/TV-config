from fastapi import FastAPI, Form
import requests
from io import BytesIO
from PIL import Image
import pytesseract

app = FastAPI()


@app.get("/search")
async def search(wd: str):
    url = f"http://cj.ffzyapi.com/api.php/provide/vod/at/xml/?wd={wd}"
    cookies = {}  # 假设cookies.txt已经加载，避免重复写入

    # 发送请求获取搜索结果
    response = requests.get(url, cookies=cookies)
    if "captcha" in response.text:  # 检查是否包含验证码
        # 找到验证码的URL
        captcha_url = response.text.split('href="')[1].split('"')[0]
        captcha_url = f"http://cj.ffzyapi.com{captcha_url}"

        # 获取验证码图片
        captcha_img_response = requests.get(captcha_url)
        img = Image.open(BytesIO(captcha_img_response.content))

        # 保存验证码图片（用作调试）
        img.save("captcha_image.png")
        return {"status": "captcha", "message": "验证码已保存", "captcha_url": captcha_url}

    return {"status": "ok", "message": "没有检测到验证码"}