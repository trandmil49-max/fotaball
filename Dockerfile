# Bu dosya, Railway'e botun çalışması için gereken her şeyi
# (Python + ffmpeg + tesseract) EKSİKSİZ ve GARANTİLİ şekilde nasıl
# kuracağını söylüyor. Bu dosyaya dokunmana gerek yok.

FROM python:3.11-slim

# Botun ihtiyaç duyduğu sistem programları: ffmpeg (video işleme),
# tesseract-ocr (skor kutusundaki yazıyı okuma), libgl1 (görüntü işleme
# kütüphanesinin ihtiyaç duyduğu bir sistem dosyası)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    tesseract-ocr \
    libgl1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /app/tmp

CMD ["python", "bot.py"]
