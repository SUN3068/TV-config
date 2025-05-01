from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import JSONResponse
from PIL import Image
import pytesseract
import requests
from io import BytesIO
from bs4 import BeautifulSoup

app = FastAPI()

session = requests.Session()


@app.post("/ocr")
async def ocr_api(file: UploadFile = File(...)):
    try:
        image = Image.open(BytesIO(await file.read()))
        code = pytesseract.image_to_string(image).strip()
        return {"code": code}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.get("/search")
def search(wd: str):
    search_url = f"http://cj.ffzyapi.com/api.php/provide/vod/at/xml/?wd={wd}"
    r = session.get(search_url, allow_redirects=False)

    if r.status_code in [301, 302] and "/WAF/VERIFY/CAPTCHA" in r.headers.get("Location", ""):
        # 被重定向了，进入验证码流程
        captcha_page_url = "http://cj.ffzyapi.com" + r.headers["Location"]
        html = session.get(captcha_page_url).text
        soup = BeautifulSoup(html, "html.parser")
        img_tag = soup.find("img")
        if not img_tag:
            return {"error": "验证码图片未找到"}

        img_url = "http://cj.ffzyapi.com" + img_tag["src"]
        img_resp = session.get(img_url)
        img = Image.open(BytesIO(img_resp.content))
        code = pytesseract.image_to_string(img).strip()

        # 查找 form 中的参数
        input_tags = soup.find_all("input")
        form_data = {i["name"]: i.get("value", "") for i in input_tags if "name" in i.attrs}
        form_data["captcha"] = code

        verify_url = captcha_page_url  # 表单 action 是当前 URL
        verify_resp = session.post(verify_url, data=form_data)

        # 成功后再次搜索
        final_resp = session.get(search_url)
        return {"status": "captcha passed", "xml": final_resp.text[:500]}

    # 没有验证码，直接返回搜索结果
    return {"status": "ok", "xml": r.text[:500]}