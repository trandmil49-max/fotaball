"""
overlay_generator.py
---------------------
Bu dosyanın görevi: ocr_reader'ın bulduğu gol anlarını alıp,
yeşil ekranlı, logolu, skorlu bir video üretmek.

Mantık:
- Maç boyunca skor birkaç kez değişir (gol anları).
- Her skor değişiminden bir sonraki değişime kadar olan süre için
  SABİT bir görsel kullanırız (skor sürekli aynı kaldığı için).
- Bu sabit görselleri arka arkaya ekleyip, orijinal video ile
  AYNI SÜREDE biten tek bir video oluştururuz.
"""

import os
import logging
from PIL import Image, ImageDraw, ImageFont
from moviepy import ImageClip, concatenate_videoclips

from config import (
    CHROMA_GREEN,
    OUTPUT_WIDTH,
    OUTPUT_HEIGHT,
    FONT_PATH,
    TEMP_DIR,
)

logger = logging.getLogger(__name__)

LOGO_SIZE = 220
BOX_TOP = 90

_font_warning_shown = False


def _load_font(size: int):
    """Font dosyasını yükler. Bir sebeple bulunamazsa (örnek: GitHub'a
    yüklerken fonts klasörü eksik kalmışsa) bot çökmesin diye
    Pillow'un kendi standart fontuna geri döner ve bunu net şekilde loglar."""
    global _font_warning_shown
    try:
        return ImageFont.truetype(FONT_PATH, size)
    except Exception:
        if not _font_warning_shown:
            logger.error(
                "UYARI: Font dosyası bulunamadı (%s). GitHub reposunda "
                "'fonts/BebasNeue-Regular.ttf' dosyasının gerçekten var "
                "olduğunu kontrol et. Şimdilik yedek/standart font kullanılıyor.",
                FONT_PATH,
            )
            _font_warning_shown = True
        return ImageFont.load_default(size=size)


def _make_frame_image(logo1: Image.Image, logo2: Image.Image, score, stage_label):
    """Tek bir skor durumunu gösteren yeşil ekranlı görseli oluşturur."""
    img = Image.new("RGB", (OUTPUT_WIDTH, OUTPUT_HEIGHT), CHROMA_GREEN)
    draw = ImageDraw.Draw(img)

    center_x = OUTPUT_WIDTH // 2

    # Varsa üstte küçük "FINAL" / "SEMIFINAL" yazısı
    y = BOX_TOP
    if stage_label:
        stage_font = _load_font(46)
        bbox = draw.textbbox((0, 0), stage_label, font=stage_font)
        w = bbox[2] - bbox[0]
        draw.text((center_x - w / 2, y), stage_label, font=stage_font, fill="white")
        y += 70

    logo_y = y + 20

    # Sol logo
    img.paste(logo1, (center_x - LOGO_SIZE - 140, logo_y), logo1)
    # Sağ logo
    img.paste(logo2, (center_x + 140, logo_y), logo2)

    # Ortadaki skor kutusu
    score_text = f"{score[0]} - {score[1]}"
    score_font = _load_font(110)
    bbox = draw.textbbox((0, 0), score_text, font=score_font)
    w = bbox[2] - bbox[0]
    h = bbox[3] - bbox[1]
    score_y = logo_y + (LOGO_SIZE / 2) - (h / 2) - 10
    draw.text((center_x - w / 2, score_y), score_text, font=score_font, fill="white")

    return img


def _prepare_logo(path: str) -> Image.Image:
    logo = Image.open(path).convert("RGBA")
    logo.thumbnail((LOGO_SIZE, LOGO_SIZE))
    # Ortalamak için kare bir tuval üzerine yerleştir
    square = Image.new("RGBA", (LOGO_SIZE, LOGO_SIZE), (0, 0, 0, 0))
    offset = ((LOGO_SIZE - logo.width) // 2, (LOGO_SIZE - logo.height) // 2)
    square.paste(logo, offset, logo)
    return square


def build_overlay_video(logo1_path: str, logo2_path: str, analysis: dict, output_path: str):
    """
    analysis: ocr_reader.analyze_video() çıktısı
    Sonuç olarak output_path'e bir .mp4 dosyası yazar.
    """
    logo1 = _prepare_logo(logo1_path)
    logo2 = _prepare_logo(logo2_path)

    events = analysis["events"]
    duration = analysis["duration"] or (events[-1][0] + 5)
    stage_label = analysis["stage_label"]

    clips = []
    for i, (start_time, score) in enumerate(events):
        end_time = events[i + 1][0] if i + 1 < len(events) else duration
        segment_duration = max(end_time - start_time, 0.1)

        frame_img = _make_frame_image(logo1, logo2, score, stage_label)
        frame_path = os.path.join(TEMP_DIR, f"segment_{i}.png")
        frame_img.save(frame_path)

        clip = ImageClip(frame_path).with_duration(segment_duration)
        clips.append(clip)

    final_clip = concatenate_videoclips(clips, method="compose")
    final_clip.write_videofile(
        output_path,
        fps=25,
        codec="libx264",
        audio=False,
        preset="medium",
        logger=None,
    )

    # Geçici kare dosyalarını temizle
    for i in range(len(events)):
        frame_path = os.path.join(TEMP_DIR, f"segment_{i}.png")
        if os.path.exists(frame_path):
            os.remove(frame_path)

    return output_path
