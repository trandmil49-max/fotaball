"""
bot.py
------
Botun kullanıcıyla konuştuğu ana dosya.

Kullanıcı için akış şu şekilde:
1. /start yazar, bot ne yapması gerektiğini anlatır.
2. Kullanıcı maç videosunun LİNKİNİ gönderir (bot videoyu buradan indirir -
   Telegram'a yüklenen dosyalar 20 MB'ı geçerse bot indiremiyor, o yüzden
   asıl işlemi linkten yapıyoruz).
3. Eğer link çalışmazsa (özel video, indirilemeyen bir site vb.), bot
   videoyu doğrudan Telegram'dan yüklemeni ister (bu durumda video
   20 MB'dan küçük olmalı).
4. Bot birinci takımın logosunu ister.
5. Bot ikinci takımın logosunu ister.
6. Bot videoyu analiz edip yeşil ekranlı skor videosunu üretir ve geri gönderir.
"""

import os
import logging

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)

from config import BOT_TOKEN, TEMP_DIR
from ocr_reader import analyze_video, detect_stage_label
from overlay_generator import build_overlay_video
from utils import fetch_video_metadata, download_video

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# Konuşmanın hangi aşamasında olduğumuzu tutan durumlar
WAITING_LINK, WAITING_VIDEO_FALLBACK, WAITING_LOGO1, WAITING_LOGO2 = range(4)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text(
        "Merhaba! Maç özeti videonu gönder, sana yeşil ekranlı skor grafiği hazırlayayım.\n\n"
        "Adım 1/3: Şimdi maç videosunun linkini gönder (YouTube linki)."
    )
    return WAITING_LINK


async def receive_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Bu fonksiyon hem /start sonrası hem de direkt link atıldığında
    # çalışabiliyor, o yüzden her ihtimalde eski verileri temizleyelim.
    context.user_data.clear()

    url = (update.message.text or "").strip()
    if not url.startswith("http"):
        await update.message.reply_text("Bu bir link gibi görünmüyor. Lütfen geçerli bir video linki gönder.")
        return WAITING_LINK

    context.user_data["video_url"] = url

    await update.message.reply_text("Video linkten indiriliyor, biraz bekle...")

    video_path = os.path.join(TEMP_DIR, f"{update.effective_chat.id}_video.mp4")
    try:
        download_video(url, video_path)
        context.user_data["video_path"] = video_path
        await update.message.reply_text(
            "Video indirildi.\n\nAdım 2/3: Birinci takımın logosunu gönder (fotoğraf olarak)."
        )
        return WAITING_LOGO1
    except Exception:
        logger.exception("Linkten video indirilemedi")
        await update.message.reply_text(
            "Bu linkten videoyu indiremedim (video özel olabilir ya da site desteklenmiyor olabilir).\n\n"
            "Bunun yerine videoyu doğrudan buraya yükler misin? "
            "(Not: Telegram kuralı gereği bot, 20 MB'dan büyük dosyaları indiremiyor, "
            "o yüzden video küçükse bu yöntem işe yarar.)"
        )
        return WAITING_VIDEO_FALLBACK


async def receive_video_fallback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    video = update.message.video or update.message.document
    if not video:
        await update.message.reply_text("Bir video dosyası göndermen lazım. Tekrar dener misin?")
        return WAITING_VIDEO_FALLBACK

    video_path = os.path.join(TEMP_DIR, f"{update.effective_chat.id}_video.mp4")
    try:
        file = await context.bot.get_file(video.file_id)
        await file.download_to_drive(video_path)
    except Exception:
        logger.exception("Telegram'dan video indirilemedi")
        await update.message.reply_text(
            "Bu video da indirilemedi - muhtemelen 20 MB sınırını aşıyor. "
            "Videoyu biraz sıkıştırıp (küçültüp) tekrar gönderebilir misin?"
        )
        return WAITING_VIDEO_FALLBACK

    context.user_data["video_path"] = video_path
    await update.message.reply_text("Video alındı.\n\nAdım 2/3: Birinci takımın logosunu gönder.")
    return WAITING_LOGO1


async def receive_logo1(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photo = update.message.photo[-1] if update.message.photo else update.message.document
    if not photo:
        await update.message.reply_text("Bir logo görseli göndermen lazım. Tekrar dener misin?")
        return WAITING_LOGO1

    file = await context.bot.get_file(photo.file_id)
    logo_path = os.path.join(TEMP_DIR, f"{update.effective_chat.id}_logo1.png")
    await file.download_to_drive(logo_path)
    context.user_data["logo1_path"] = logo_path

    await update.message.reply_text("Adım 3/3: Şimdi ikinci takımın logosunu gönder.")
    return WAITING_LOGO2


async def receive_logo2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photo = update.message.photo[-1] if update.message.photo else update.message.document
    if not photo:
        await update.message.reply_text("Bir logo görseli göndermen lazım. Tekrar dener misin?")
        return WAITING_LOGO2

    file = await context.bot.get_file(photo.file_id)
    logo_path = os.path.join(TEMP_DIR, f"{update.effective_chat.id}_logo2.png")
    await file.download_to_drive(logo_path)
    context.user_data["logo2_path"] = logo_path

    await update.message.reply_text(
        "Her şey tamam! Video hazırlanıyor, videonun uzunluğuna göre birkaç dakika "
        "sürebilir. Lütfen bekle, bitince buraya göndereceğim."
    )

    await process_and_send(update, context)
    return ConversationHandler.END


async def process_and_send(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    video_path = context.user_data["video_path"]
    logo1_path = context.user_data["logo1_path"]
    logo2_path = context.user_data["logo2_path"]
    video_url = context.user_data.get("video_url", "")

    try:
        analysis = analyze_video(video_path)

        # Skor kutusunda final/yarı final bulunamadıysa, linkten gelen
        # başlık/açıklamaya da bakalım.
        if not analysis["stage_label"] and video_url:
            metadata_text = fetch_video_metadata(video_url)
            analysis["stage_label"] = detect_stage_label(metadata_text)

        output_path = os.path.join(TEMP_DIR, f"{chat_id}_output.mp4")
        build_overlay_video(logo1_path, logo2_path, analysis, output_path)

        events = analysis["events"]
        summary_lines = [f"{int(t // 60)}:{int(t % 60):02d} -> {s[0]}-{s[1]}" for t, s in events]
        summary = "\n".join(summary_lines)

        await context.bot.send_message(
            chat_id,
            f"Tespit edilen skor değişimleri:\n{summary}\n\n"
            "Eğer bunlar yanlışsa, videonun üstündeki skor kutusu farklı bir yerde "
            "olabilir - bana haber ver, ayarı düzeltelim."
        )

        with open(output_path, "rb") as f:
            await context.bot.send_video(chat_id, video=f, caption="Yeşil ekranlı skor grafiğin hazır!")

    except Exception as e:
        logger.exception("İşlem sırasında hata oluştu")
        await context.bot.send_message(
            chat_id,
            f"Bir sorun oldu, video işlenemedi. Hata: {e}\n\n"
            "Tekrar denemek için /start yazabilirsin."
        )
    finally:
        for key in ("video_path", "logo1_path", "logo2_path"):
            path = context.user_data.get(key)
            if path and os.path.exists(path):
                os.remove(path)


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("İşlem iptal edildi. Baştan başlamak için /start yaz.")
    return ConversationHandler.END


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    """Beklenmeyen bir hata olursa sessizce takılıp kalmak yerine loglayıp
    mümkünse kullanıcıya haber veriyoruz."""
    logger.error("Beklenmeyen hata:", exc_info=context.error)
    if isinstance(update, Update) and update.effective_chat:
        try:
            await context.bot.send_message(
                update.effective_chat.id,
                "Beklenmeyen bir hata oldu. Tekrar denemek için /start yazabilirsin.",
            )
        except Exception:
            pass


def main():
    if not BOT_TOKEN:
        raise RuntimeError(
            "BOT_TOKEN bulunamadı. Railway'de 'Variables' kısmına BOT_TOKEN eklemen lazım."
        )

    app = Application.builder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("start", start),
            # Kullanıcı /start yazmadan direkt bir link gönderirse de
            # bot otomatik olarak başlasın diye ikinci bir giriş noktası.
            MessageHandler(filters.Regex(r"^https?://\S+") & filters.TEXT, receive_link),
        ],
        states={
            WAITING_LINK: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_link)],
            WAITING_VIDEO_FALLBACK: [
                MessageHandler(filters.VIDEO | filters.Document.VIDEO, receive_video_fallback)
            ],
            WAITING_LOGO1: [MessageHandler(filters.PHOTO | filters.Document.IMAGE, receive_logo1)],
            WAITING_LOGO2: [MessageHandler(filters.PHOTO | filters.Document.IMAGE, receive_logo2)],
        },
        fallbacks=[CommandHandler("cancel", cancel), CommandHandler("start", start)],
    )

    app.add_handler(conv_handler)
    app.add_error_handler(error_handler)

    logger.info("Bot başlatıldı, Telegram'dan mesaj bekleniyor...")
    app.run_polling()


if __name__ == "__main__":
    main()
