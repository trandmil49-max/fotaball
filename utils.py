"""
utils.py
--------
Kullanıcının verdiği YouTube linkinden video başlığını/açıklamasını
ve videonun kendisini indirmeye yarayan yardımcı fonksiyonlar.

Videoyu Telegram üzerinden değil, doğrudan linkten indiriyoruz çünkü
Telegram'ın kendi kuralı: bir bot, Telegram'a yüklenen dosyaları
sadece 20 MB'a kadar indirebiliyor. Link üzerinden indirince bu
sınıra hiç takılmıyoruz.

ÖNEMLİ NOT: YouTube, Railway gibi sunucu/veri merkezi adreslerinden
gelen istekleri bazen "bot" sanıp engelliyor ("Sign in to confirm
you're not a bot" gibi hatalar verir). Bunu aşmak için indirme
isteğini bir telefon uygulamasıymış gibi göndermeyi deniyoruz -
bu genelde işe yarıyor. Yine de bazı videolarda (yaş sınırlı,
bölgeye özel vb.) engel devam edebilir; o yüzden farklı yöntemleri
sırayla deniyoruz.
"""

import os
import logging
import yt_dlp

logger = logging.getLogger(__name__)

# YouTube'un "bot" sanıp engellemesini aşmak için sırayla denenecek
# farklı "istemci" kimlikleri. Biri engellenirse diğerini deniyoruz.
_CLIENT_ATTEMPTS = ["android", "ios", "web_embedded", "tv"]


def fetch_video_metadata(url: str) -> str:
    """Başlık + açıklamayı tek bir metin olarak döner. Hata olursa boş string döner."""
    if not url:
        return ""
    for client in _CLIENT_ATTEMPTS:
        try:
            options = {
                "quiet": True,
                "skip_download": True,
                "noplaylist": True,
                "extractor_args": {"youtube": {"player_client": [client]}},
            }
            with yt_dlp.YoutubeDL(options) as ydl:
                info = ydl.extract_info(url, download=False)
            title = info.get("title", "") or ""
            description = info.get("description", "") or ""
            return f"{title}\n{description}"
        except Exception:
            continue
    return ""


def download_video(url: str, output_path: str) -> str:
    """
    Verilen linkten videoyu indirip output_path'e kaydeder.

    YouTube'un sunucu tabanlı isteklere karşı koyduğu engeli aşmak için
    birkaç farklı yöntemi sırayla deniyoruz. Hepsi başarısız olursa,
    EN SON denenen gerçek hatayı fırlatıyoruz (tahmin değil, gerçek
    hata) - böylece Railway loglarında ne olduğunu net görebiliriz.
    """
    cookies_file = _write_cookies_file_if_configured()

    last_error = None
    for client in _CLIENT_ATTEMPTS:
        options = {
            "quiet": True,
            "noplaylist": True,
            "format": "best[height<=720][ext=mp4]/best[height<=720]/best",
            "outtmpl": output_path,
            "merge_output_format": "mp4",
            "extractor_args": {"youtube": {"player_client": [client]}},
        }
        if cookies_file:
            options["cookiefile"] = cookies_file

        try:
            if os.path.exists(output_path):
                os.remove(output_path)
            with yt_dlp.YoutubeDL(options) as ydl:
                ydl.download([url])
            if os.path.exists(output_path):
                return output_path
        except Exception as e:
            last_error = e
            logger.warning("İndirme denemesi başarısız oldu (client=%s): %s", client, e)
            continue

    # Hiçbiri işe yaramadıysa, en son gerçek hatayı fırlat (tahmin uydurmuyoruz)
    raise RuntimeError(f"Video hiçbir yöntemle indirilemedi. Son hata: {last_error}")


def _write_cookies_file_if_configured():
    """
    İsteğe bağlı: Railway'de YTDLP_COOKIES adında bir değişken varsa
    (tarayıcından dışa aktardığın cookies.txt içeriği), bunu geçici bir
    dosyaya yazıp yt-dlp'ye veriyoruz. Bu, "sign in to confirm you're
    not a bot" gibi inatçı engelleri aşmanın en kesin yolu.
    Bu değişken yoksa sorun değil, cookies olmadan da denenir.
    """
    cookies_content = os.environ.get("YTDLP_COOKIES", "")
    if not cookies_content:
        return None
    cookies_path = "/tmp/yt_cookies.txt"
    try:
        with open(cookies_path, "w") as f:
            f.write(cookies_content)
        return cookies_path
    except Exception:
        return None

