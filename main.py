import os
import logging
import pytz
import requests
import time
import asyncio
from datetime import time as dt_time
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# --- Konfigurasi ---
TOKEN = "8152147538:AAH-hjZW1db5o6obJv41Skm3NRNk1xMfoTQ"
TARGET_CHAT_ID = "6655121882"
LOOKER_STUDIO_MSA_WSA_URL = "https://lookerstudio.google.com/s/tR0woFxlU6g"
LOOKER_STUDIO_PILATEN_URL = "https://lookerstudio.google.com/s/sw2UI-AT_Yw"
SCREENSHOT_API_KEY = "431NH5K-ZN7M81P-N350RHD-XTZF3SN"
SCREENSHOT_API_URL = "https://shot.screenshotapi.net/screenshot"
TIMEZONE = pytz.timezone("Asia/Jakarta")

# --- Logging ---
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- Fungsi Screenshot ---
def get_looker_studio_screenshot(looker_studio_url: str, output_filename: str) -> str | None:
    params = {
        "token": SCREENSHOT_API_KEY,
        "url": looker_studio_url,
        "width": 1920,
        "height": 1080,
        "full_page": "true",
        "delay": 5000,
        "click_to_crop": "true",
        "element": "#page-0"
    }

    try:
        response = requests.get(SCREENSHOT_API_URL, params=params, stream=True)
        response.raise_for_status()
        response_json = response.json()

        logger.info(f"Screenshot API response: {response_json}")

        image_url = response_json.get("screenshot")
        if not image_url:
            logger.error("❌ Tidak ada URL screenshot ditemukan.")
            return None

        time.sleep(3)

        image_data = requests.get(image_url, stream=True)
        image_data.raise_for_status()

        with open(output_filename, "wb") as f:
            for chunk in image_data.iter_content(8192):
                f.write(chunk)

        return output_filename

    except Exception as e:
        logger.error(f"❌ Gagal mengambil screenshot: {e}")
        return None

# --- Command Handlers ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Halo! Berikut daftar perintah:\n"
        "/msawsa - Kirim snapshot dashboard MSA/WSA\n"
        "/pilaten - Kirim snapshot dashboard PI LATEN"
    )

async def msawsa(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔄 Sedang mengambil snapshot dashboard MSA/WSA...")
    path = get_looker_studio_screenshot(LOOKER_STUDIO_MSA_WSA_URL, "msawsa.png")
    if path and os.path.exists(path):
        with open(path, "rb") as f:
            await update.message.reply_photo(f, caption="Laporan MSA/WSA")
        os.remove(path)
    else:
        await update.message.reply_text("❌ Gagal mengambil screenshot dashboard MSA/WSA.")

async def pilaten(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔄 Sedang mengambil snapshot dashboard PI LATEN...")
    path = get_looker_studio_screenshot(LOOKER_STUDIO_PILATEN_URL, "pilaten.png")
    if path and os.path.exists(path):
        with open(path, "rb") as f:
            await update.message.reply_photo(f, caption="Laporan PI LATEN")
        os.remove(path)
    else:
        await update.message.reply_text("❌ Gagal mengambil screenshot dashboard PI LATEN.")

# --- Kirim Otomatis Gabungan ---
async def send_all_snapshots(context: ContextTypes.DEFAULT_TYPE):
    # --- MSA/WSA ---
    path1 = get_looker_studio_screenshot(LOOKER_STUDIO_MSA_WSA_URL, "auto_msawsa.png")
    if path1 and os.path.exists(path1):
        with open(path1, "rb") as f:
            await context.bot.send_photo(
                chat_id=TARGET_CHAT_ID,
                photo=f,
                caption="🔔 *Snapshot (Otomatis) MSA/WSA*",
                parse_mode="Markdown"
            )
        os.remove(path1)
    else:
        logger.error("❌ Gagal kirim otomatis MSA/WSA")

    # Delay sebelum kirim PI LATEN
    await asyncio.sleep(5)

    # --- PI LATEN ---
    path2 = get_looker_studio_screenshot(LOOKER_STUDIO_PILATEN_URL, "auto_pilaten.png")
    if path2 and os.path.exists(path2):
        with open(path2, "rb") as f:
            await context.bot.send_photo(
                chat_id=TARGET_CHAT_ID,
                photo=f,
                caption="🔔 *Snapshot (Otomatis) PI LATEN*",
                parse_mode="Markdown"
            )
        os.remove(path2)
    else:
        logger.error("❌ Gagal kirim otomatis PI LATEN")

# --- Fungsi Utama ---
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("msawsa", msawsa))
    app.add_handler(CommandHandler("pilaten", pilaten))

    job_queue = app.job_queue
    time_morning = dt_time(9, 0, tzinfo=TIMEZONE)
    time_evening = dt_time(16, 42, tzinfo=TIMEZONE)

    job_queue.run_daily(send_all_snapshots, time=time_morning)
    job_queue.run_daily(send_all_snapshots, time=time_evening)

    logger.info("Bot dimulai dengan jadwal otomatis.")
    app.run_polling()

if __name__ == "__main__":
    main()
