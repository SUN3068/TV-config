from flask import Flask, request, jsonify
import requests
from PIL import Image
import pytesseract
from io import BytesIO

app = Flask(__name__)

@app.route('/ocr', methods=['POST'])
def ocr():
    data = request.json
    url = data.get("url")
    if not url:
        return jsonify({"error": "No image URL provided"}), 400

    try:
        response = requests.get(url, timeout=10)
        img = Image.open(BytesIO(response.content)).convert("L")
        code = pytesseract.image_to_string(img, config="--psm 7 digits").strip()
        return jsonify({"code": code})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/')
def index():
    return "OCR API is running."

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)