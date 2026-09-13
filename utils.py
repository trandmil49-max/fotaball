"""
utils.py
--------
Kullanıcının verdiği YouTube linkinden video başlığını ve açıklamasını
çeker. Bu bilgi, "final mi yarı final mi" gibi ek bir doğrulama için
kullanılır (skor kutusundan bulunamazsa yedek kaynak olur).
Link verilmezse ya da bilgi çekilemezse sorun değil, bot skor kutusu
okumasıyla devam eder.
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
