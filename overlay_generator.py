"""
overlay_generator.py
---------------------
Bu dosyanın görevi: ocr_reader'ın bulduğu gol anlarını alıp,
yeşil ekranlı, logolu, skorlu bir video üretmek.

Önceki versiyon "moviepy" adlı bir kütüphane kullanıyordu, ama Railway'in
sınırlı hafızasında bazen çöküyordu ("Broken pipe" hatası). Bu yüzden
artık videoyu doğrudan ve daha hafif bir şekilde ffmpeg programına
kendimiz komut vererek oluşturuyoruz - bu hem daha az hafıza kullanıyor
hem de çok daha az hata veriyor.

Mantık:
- Maç boyunca skor birkaç kez değişir (gol anları).
- Her skor değişiminden bir sonraki değişime kadar olan süre için
  SABİT bir görsel kullanırız (skor sürekli aynı kaldığı için).
- Bu sabit görselleri, süreleriyle birlikte ffmpeg'e veriyoruz, o da
  bunları birleştirip tek bir video haline getiriyor.
"""

import os
import subprocess
import logging
from PIL import Image, ImageDraw, ImageFont

from config import (
    CHROMA_GREEN,
    OUTPUT_WIDTH,
    OUTPUT_HEIGHT,
    FONT_PATH,
    TEMP_DIR,
)

logger = logging.getLogger(__name__)

LOGO_SIZE = 230
# Logoların merkezden ne kadar uzakta duracağı (referans görseldeki gibi yakın)
LOGO_GAP_FROM_CENTER = 195
CENTER_Y = 260  # Logoların ve skorun dikey olarak hizalanacağı ORTAK çizgi

_font_warning_shown = False


def _load_font(size: int):
    """Font dosyasını yükler. Bir sebeple bulunamazsa bot çökmesin diye
    Pillow'un kendi standart fontuna geri döner."""
    global _font_warning_shown
    try:
        return ImageFont.truetype(FONT_PATH, size)
    except Exception:
        if not _font_warning_shown:
            logger.error(
                "UYARI: Font dosyası bulunamadı (%s). GitHub reposunda "
                "'fonts' klasörünün gerçekten yüklendiğini kontrol et. "
                "Şimdilik yedek/standart font kullanılıyor.",
                FONT_PATH,
            )
            _font_warning_shown = True
        return ImageFont.load_default(size=size)


def _remove_white_background(img: Image.Image, threshold: int = 235) -> Image.Image:
    """Logonun arkasındaki beyaz zemini şeffaf yapar, böylece yeşil ekranda
    logonun etrafında beyaz kutu görünmez."""
    img = img.convert("RGBA")
    pixels = img.load()
    width, height = img.size
    for y in range(height):
        for x in range(width):
            r, g, b, a = pixels[x, y]
            if r > threshold and g > threshold and b > threshold:
                pixels[x, y] = (r, g, b, 0)
    return img


def _prepare_logo(path: str) -> Image.Image:
    logo = Image.open(path).convert("RGBA")
    logo.thumbnail((LOGO_SIZE, LOGO_SIZE))
    logo = _remove_white_background(logo)
    # Ortalamak için kare bir tuval üzerine yerleştir - böylece her logo
    # aynı boyuttaki kutunun TAM ORTASINDA durur (biri büyük biri küçük
    # görünmesin, hepsi aynı çizgide dursun diye).
    square = Image.new("RGBA", (LOGO_SIZE, LOGO_SIZE), (0, 0, 0, 0))
    offset = ((LOGO_SIZE - logo.width) // 2, (LOGO_SIZE - logo.height) // 2)
    square.paste(logo, offset, logo)
    return square


def _make_frame_image(logo1: Image.Image, logo2: Image.Image, score, stage_label):
    """Tek bir skor durumunu gösteren yeşil ekranlı görseli oluşturur.
    Her şey (logolar, skor/VS yazısı) CENTER_Y çizgisine göre tam ortalanır,
    böylece biri yukarıda biri aşağıda gibi kaymaz."""
    img = Image.new("RGB", (OUTPUT_WIDTH, OUTPUT_HEIGHT), CHROMA_GREEN)
    draw = ImageDraw.Draw(img)

    center_x = OUTPUT_WIDTH // 2

    # Varsa üstte küçük "FINAL" / "SEMIFINAL" yazısı
    if stage_label:
        stage_font = _load_font(46)
        draw.text(
            (center_x, CENTER_Y - LOGO_SIZE // 2 - 55),
            stage_label,
            font=stage_font,
            fill="white",
            anchor="mm",
        )

    # Sol logo - dikey olarak CENTER_Y çizgisine göre ortalanmış
    logo1_y = CENTER_Y - LOGO_SIZE // 2
    img.paste(logo1, (center_x - LOGO_GAP_FROM_CENTER - LOGO_SIZE, logo1_y), logo1)

    # Sağ logo - aynı çizgide
    img.paste(logo2, (center_x + LOGO_GAP_FROM_CENTER, logo1_y), logo2)

    # Ortadaki yazı: maç başlamadan (0-0) "VS", gol olduktan sonra gerçek skor
    if score == (0, 0):
        center_text = "VS"
        center_font = _load_font(95)
    else:
        center_text = f"{score[0]} - {score[1]}"
        center_font = _load_font(105)

    # anchor="mm" (middle-middle): yazının TAM ORTASI, verdiğimiz noktaya
    # denk gelir - böylece logolarla aynı yatay çizgide durur.
    draw.text((center_x, CENTER_Y), center_text, font=center_font, fill="white", anchor="mm")

    return img


def build_overlay_video(logo1_path: str, logo2_path: str, analysis: dict, output_path: str):
    """
    analysis: ocr_reader.analyze_video() çıktısı
    Sonuç olarak output_path'e bir .mp4 dosyası yazar.
    Hata olursa RuntimeError fırlatır, çağıran taraf (bot.py) bunu
    yakalayıp kullanıcıya haber verir.
    """
    try:
        logo1 = _prepare_logo(logo1_path)
        logo2 = _prepare_logo(logo2_path)
    except Exception as e:
        raise RuntimeError(f"Logo dosyası işlenemedi (bozuk/eksik indirilmiş olabilir): {e}")

    events = analysis["events"]
    duration = analysis["duration"] or (events[-1][0] + 5)
    stage_label = analysis["stage_label"]

    concat_list_path = os.path.join(TEMP_DIR, os.path.basename(output_path) + "_list.txt")
    frame_paths = []

    with open(concat_list_path, "w") as list_file:
        for i, (start_time, score) in enumerate(events):
            end_time = events[i + 1][0] if i + 1 < len(events) else duration
            segment_duration = max(end_time - start_time, 0.1)

            frame_img = _make_frame_image(logo1, logo2, score, stage_label)
            frame_path = os.path.join(TEMP_DIR, f"{os.path.basename(output_path)}_seg{i}.png")
            frame_img.save(frame_path)
            frame_paths.append(frame_path)

            list_file.write(f"file '{frame_path}'\n")
            list_file.write(f"duration {segment_duration}\n")

        # ffmpeg'in "concat" kuralı gereği: son dosya süresi olmadan bir
        # kere daha tekrar yazılmalı, yoksa ffmpeg son sahneyi görmezden gelir.
        if frame_paths:
            list_file.write(f"file '{frame_paths[-1]}'\n")

    cmd = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", concat_list_path,
        "-vf", "fps=25,format=yuv420p",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-r", "25",
        output_path,
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    # Geçici dosyaları temizle
    for p in frame_paths:
        if os.path.exists(p):
            os.remove(p)
    if os.path.exists(concat_list_path):
        os.remove(concat_list_path)

    if result.returncode != 0 or not os.path.exists(output_path):
        # ffmpeg'in verdiği son birkaç satır hatayı hem loglara hem de
        # kullanıcıya gösterilecek mesaja koyuyoruz - böylece Railway
        # loglarına bakmaya gerek kalmadan gerçek sebep görülebilir.
        error_tail = "\n".join(result.stderr.strip().splitlines()[-8:])
        logger.error("FFmpeg videoyu oluşturamadı:\n%s", error_tail)
        raise RuntimeError(f"ffmpeg hatası: {error_tail[:600]}")

    return output_path
