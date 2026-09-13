"""
utils.py
--------
Kullanıcının verdiği YouTube linkinden video başlığını/açıklamasını
ve videonun kendisini indirmeye yarayan yardımcı fonksiyonlar.

Videoyu Telegram üzerinden değil, doğrudan linkten indiriyoruz çünkü
Telegram'ın kendi kuralı: bir bot, Telegram'a yüklenen dosyaları
sadece 20 MB'a kadar indirebiliyor. Link üzerinden indirince bu
sınıra hiç takılmıyoruz.
"""

import yt_dlp


def fetch_video_metadata(url: str) -> str:
    """Başlık + açıklamayı tek bir metin olarak döner. Hata olursa boş string döner."""
    if not url:
        return ""
    try:
        options = {"quiet": True, "skip_download": True, "noplaylist": True}
        with yt_dlp.YoutubeDL(options) as ydl:
            info = ydl.extract_info(url, download=False)
        title = info.get("title", "") or ""
        description = info.get("description", "") or ""
        return f"{title}\n{description}"
    except Exception:
        return ""


def download_video(url: str, output_path: str) -> str:
    """
    Verilen linkten videoyu indirip output_path'e kaydeder.
    Başarılı olursa dosya yolunu, olmazsa hatayı fırlatır (raise eder) -
    çağıran taraf bunu yakalayıp kullanıcıya haber verir.
    """
    options = {
        "quiet": True,
        "noplaylist": True,
        "format": "best[height<=720][ext=mp4]/best[height<=720]/best",
        "outtmpl": output_path,
        "merge_output_format": "mp4",
    }
    with yt_dlp.YoutubeDL(options) as ydl:
        ydl.download([url])
    return output_path

