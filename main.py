from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
import pytesseract
from PIL import Image
import io

app = FastAPI()

@app.post("/ocr")
async def ocr_image(file: UploadFile = File(...)):
    try:
        # 读取上传的图像内容并转为 PIL Image
        contents = await file.read()
        image = Image.open(io.BytesIO(contents))

        # 使用 Tesseract 识别图像中的文字
        text = pytesseract.image_to_string(image)

        return {"code": 200, "text": text.strip()}
    except Exception as e:
        return JSONResponse(status_code=500, content={"code": 500, "error": str(e)})


@app.get("/search")
def search(key: str):
    """
    这是 TV 的搜索请求中转接口：
    - 自动识别验证码（下载验证码图 -> 识别 -> 提交验证码）
    - 然后再执行原本的搜索请求
    - 最终返回结果（xml 或 json 格式）
    """

    return {"list": []}  # TODO：填真实逻辑