"""
Genel ayarlar
--------------
Buradaki sayıları değiştirerek botun davranışını ince ayar yapabilirsin.
Kodun geri kalanına dokunmana gerek yok.
"""

import os

# Telegram bot token'ı - Railway'de "Variables" kısmına ekleyeceksin
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")

# --- Skor kutusunu videoda arama ayarları ---

# Videonun üst kısmının yüzde kaçı skor kutusunu içeriyor?
# 0.28 demek: videonun üstten %28'lik kısmına bak.
# Eğer bot skoru bulamıyorsa ilk deneyeceğin şey bu sayıyı büyütüp küçültmek.
TOP_CROP_RATIO = 0.28

# Videoyu saniyede kaç kare tarasın? (1 = saniyede 1 kez bak, yeterli ve hızlı)
SAMPLE_FPS = 1.0

# Bir skorun "gerçek" sayılması için art arda kaç kez aynı okunması lazım?
# Yüksek olursa daha güvenilir ama biraz daha yavaş olur.
CONFIRM_COUNT = 3

# --- Görsel (overlay) ayarları ---

# Saf yeşil ekran rengi (kroma yeşili) - CapCut/editör programlarının
# "arka planı kaldır" özelliğiyle sorunsuz çalışan standart ton.
CHROMA_GREEN = (0, 177, 64)

# Çıktı videosunun boyutu (dikey, TikTok/Shorts formatı)
OUTPUT_WIDTH = 1080
OUTPUT_HEIGHT = 1920

FONT_PATH = os.path.join(os.path.dirname(__file__), "fonts", "Anton-Regular.ttf")

# Geçici dosyaların tutulacağı klasör
TEMP_DIR = os.path.join(os.path.dirname(__file__), "tmp")
os.makedirs(TEMP_DIR, exist_ok=True)
