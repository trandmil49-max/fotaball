"""
ocr_reader.py
-------------
Bu dosyanın tek görevi: verilen videoyu izleyip, videonun üst kısmında
duran skor kutusundaki yazıyı okumak ve skorun ne zaman değiştiğini bulmak.

Nasıl çalışır (basitçe):
1. Videoyu saniyede 1 kere "fotoğraflıyoruz" (kare alıyoruz).
2. Her fotoğrafın sadece üst kısmını kırpıyoruz (skor kutusunun olduğu yer).
3. O kırpılmış küçük görüntüdeki yazıyı OCR (görüntüden yazı okuma) ile okuyoruz.
4. "0-2", "1-0" gibi bir skor kalıbı bulmaya çalışıyoruz.
5. Aynı skoru art arda birkaç kere görürsek, "bu gerçek, OCR yanlış okumadı"
   diyip kabul ediyoruz. Böylece bulanık bir kareden yanlış skor çıkmaz.
6. Skor bir öncekinden farklıysa, bunu "gol anı" olarak kaydediyoruz.
"""

import re
import cv2
import pytesseract

from config import TOP_CROP_RATIO, SAMPLE_FPS, CONFIRM_COUNT

# "0-2", "1 - 0", "12:3" gibi skor kalıplarını yakalayan basit bir kural
SCORE_PATTERN = re.compile(r"(\d{1,2})\s*[-:]\s*(\d{1,2})")

# Maçın aşamasını anlamak için aranacak kelimeler (İngilizce çıktı vereceğiz)
STAGE_KEYWORDS = {
    "FINAL": ["final"],
    "SEMIFINAL": ["semi final", "semi-final", "semifinal", "yarı final", "yari final"],
    "QUARTERFINAL": ["quarter final", "quarter-final", "çeyrek final", "ceyrek final"],
}


def _read_text_from_frame(frame, crop_ratio: float) -> str:
    """Bir video karesinin üst kısmını kırpıp OCR ile okur."""
    height, width = frame.shape[:2]
    crop_height = int(height * crop_ratio)
    top_region = frame[0:crop_height, 0:width]

    gray = cv2.cvtColor(top_region, cv2.COLOR_BGR2GRAY)
    # Yazıyı daha net hale getirmek için basit bir netleştirme (threshold)
    _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)

    try:
        text = pytesseract.image_to_string(thresh, config="--psm 6")
    except Exception:
        text = ""
    return text


def _extract_score(text: str):
    match = SCORE_PATTERN.search(text)
    if not match:
        return None
    return int(match.group(1)), int(match.group(2))


def detect_stage_label(all_text: str) -> str:
    """Toplanan tüm OCR metninde final/yarı final gibi bir ifade var mı bakar."""
    lowered = all_text.lower()
    for label, keywords in STAGE_KEYWORDS.items():
        for kw in keywords:
            if kw in lowered:
                return label
    return None


def analyze_video(video_path: str):
    """
    Videoyu analiz eder.

    Döndürdüğü şey:
    {
        "events": [(saniye, (takim1_skor, takim2_skor)), ...],
        "stage_label": "FINAL" / "SEMIFINAL" / None,
        "duration": video suresi (saniye),
        "fps": videonun orijinal saniyedeki kare sayisi
    }
    """
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise RuntimeError("Video açılamadı, dosya bozuk olabilir.")

    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
    duration = frame_count / fps if fps else 0

    step = max(int(fps / SAMPLE_FPS), 1)

    events = []
    all_text_chunks = []

    pending_score = None
    pending_count = 0
    confirmed_score = None

    frame_index = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        if frame_index % step == 0:
            timestamp = frame_index / fps
            text = _read_text_from_frame(frame, TOP_CROP_RATIO)
            all_text_chunks.append(text)

            score = _extract_score(text)
            if score is not None:
                if score == pending_score:
                    pending_count += 1
                else:
                    pending_score = score
                    pending_count = 1

                if pending_count >= CONFIRM_COUNT and score != confirmed_score:
                    confirmed_score = score
                    events.append((timestamp, confirmed_score))

        frame_index += 1

    cap.release()

    # Eğer hiç skor bulunamadıysa en azından 0-0 ile başlat
    if not events:
        events = [(0.0, (0, 0))]
    elif events[0][0] > 0.5:
        events.insert(0, (0.0, (0, 0)))

    stage_label = detect_stage_label(" ".join(all_text_chunks))

    return {
        "events": events,
        "stage_label": stage_label,
        "duration": duration,
        "fps": fps,
    }
