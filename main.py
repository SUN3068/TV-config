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

@app.get("/")
async def root():
    return {"msg": "OCR API Running"}