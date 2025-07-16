import os
import logging
import pytz
import asyncio
from dotenv import load_dotenv
from datetime import time as dt_time, datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
from playwright.async_api import async_playwright
from PIL import Image

# === Konfigurasi ===
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
TARGET_CHAT_ID = os.getenv("TARGET_CHAT_ID")
LOOKER_STUDIO_MSA_WSA_URL = os.getenv("LOOKER_STUDIO_MSA_WSA_URL")
LOOKER_STUDIO_PILATEN_URL = os.getenv("LOOKER_STUDIO_PILATEN_URL")
TIMEZONE = pytz.timezone("Asia/Jakarta")

# === Logging ===
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# === Section Coordinates ===
SECTION_COORDINATES = {
    "fulldashboard": (10, 10, 1234, 974),
    "fulfillmentfbb": (34, 36, 334, 293),
    "assurancefbb": (351, 114, 724, 453),
    "scorecredit": (772, 117, 1222, 267),
    "fulfillmentbges": (34, 301, 333, 551),
    "assurancebges": (34, 559, 333, 913),
    "msaassurance": (743, 268, 1219, 622),
    "msacnop": (349, 458, 722, 911),
    "msaquality": (743, 635, 1212, 911)
}

SECTION_LABELS = {
    "fulldashboard": "FULL DASHBOARD",
    "fulfillmentfbb": "FULFILLMENT FBB",
    "assurancefbb": "ASSURANCE FBB",
    "scorecredit": "SCORE CREDIT",
    "fulfillmentbges": "FULFILLMENT BGES",
    "assurancebges": "ASSURANCE BGES",
    "msaassurance": "MSA ASSURANCE",
    "msacnop": "MSA CNOP",
    "msaquality": "MSA QUALITY"
}

# === Fungsi Umum ===
def get_greeting():
    hour = datetime.now(TIMEZONE).hour
    if 5 <= hour < 12:
        return "Selamat pagi"
    elif 12 <= hour < 15:
        return "Selamat siang"
    elif 15 <= hour < 18:
        return "Selamat sore"
    return "Selamat malam"

def get_formatted_greeting_with_time():
    now = datetime.now(TIMEZONE)
    bulan = ["Januari", "Februari", "Maret", "April", "Mei", "Juni",
             "Juli", "Agustus", "September", "Oktober", "November", "Desember"]
    return f"{get_greeting()}, berikut laporan %s terbaru pada {now.day} {bulan[now.month-1]} {now.year}, {now:%H:%M} WIB"

async def get_looker_studio_screenshot(url, filename):
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(viewport={"width": 1500, "height": 1500})
            page = await context.new_page()
            await page.goto(url, timeout=60000)
            await page.wait_for_timeout(7000)
            await page.evaluate("() => { window.scrollTo(0, document.body.scrollHeight); }")
            await page.wait_for_timeout(1000)
            element = await page.query_selector("div.alignHolder")
            if element:
                await element.screenshot(path=filename)
                return filename, None
            await page.screenshot(path=filename, full_page=True)
            return filename, None
    except Exception as e:
        logger.error(f"Screenshot error: {e}")
        return None, None

# === Handlers ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [["/msawsa", "/pilaten"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)
    await update.message.reply_text(
        f"{get_greeting()}, selamat datang di Dashboard Monitoring Telkom!\n\nBerikut adalah dua laporan utama:\n/msawsa\n/pilaten",
        reply_markup=reply_markup
    )

async def send_section_buttons(chat_id: int, context: ContextTypes.DEFAULT_TYPE):
    keys = list(SECTION_COORDINATES.keys())
    keys.remove("fulldashboard")
    buttons = [
        [
            InlineKeyboardButton(SECTION_LABELS[keys[i]], callback_data=keys[i]),
            InlineKeyboardButton(SECTION_LABELS[keys[i+1]], callback_data=keys[i+1])
        ] for i in range(0, len(keys)-1, 2)
    ]
    if len(keys) % 2 == 1:
        buttons.append([InlineKeyboardButton(SECTION_LABELS[keys[-1]], callback_data=keys[-1])])

    await context.bot.send_message(
        chat_id=chat_id,
        text="Silakan pilih bagian laporan yang ingin ditampilkan:",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

async def msawsa(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Sedang mengambil laporan MSA/WSA ...")
    file, _ = await get_looker_studio_screenshot(LOOKER_STUDIO_MSA_WSA_URL, "msawsa_dashboard.png")
    if file and os.path.exists(file):
        await update.message.reply_photo(photo=open(file, "rb"))
        os.remove(file)
        await send_section_buttons(update.message.chat_id, context)
    else:
        await update.message.reply_text("Gagal mengambil laporan MSA/WSA.")

async def pilaten(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Sedang mengambil laporan PI LATEN...")
    file, _ = await get_looker_studio_screenshot(LOOKER_STUDIO_PILATEN_URL, "pilaten_base_screenshot.png")
    if file and os.path.exists(file):
        await update.message.reply_photo(open(file, "rb"), caption="Laporan: PI LATEN")
        os.remove(file)
    else:
        await update.message.reply_text("Gagal mengambil laporan PI LATEN.")

async def section_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    key = query.data
    if key not in SECTION_COORDINATES:
        return await query.edit_message_text("Bagian laporan tidak dikenali.")

    await query.edit_message_text(f"Mengambil bagian laporan: {SECTION_LABELS[key]}")

    file, _ = await get_looker_studio_screenshot(LOOKER_STUDIO_MSA_WSA_URL, f"{key}_base.png")
    if file and os.path.exists(file):
        with Image.open(file) as img:
            cropped = img.crop(SECTION_COORDINATES[key])
            crop_name = f"{key}_cropped.png"
            cropped.save(crop_name)

            with open(crop_name, "rb") as photo:
                await context.bot.send_photo(
                    chat_id=query.message.chat_id,
                    photo=photo,
                    caption=f"Laporan: {SECTION_LABELS[key]}"
                )

            os.remove(crop_name)
        os.remove(file)
        await send_section_buttons(query.message.chat_id, context)
    else:
        await context.bot.send_message(chat_id=query.message.chat_id, text="Gagal mengambil screenshot.")

async def send_all_snapshots(context: ContextTypes.DEFAULT_TYPE):
    caption = get_formatted_greeting_with_time()
    file1, _ = await get_looker_studio_screenshot(LOOKER_STUDIO_MSA_WSA_URL, "auto_msawsa.png")
    if file1 and os.path.exists(file1):
        await context.bot.send_photo(chat_id=TARGET_CHAT_ID, photo=open(file1, "rb"), caption=caption % "MSA/WSA")
        os.remove(file1)
    await asyncio.sleep(5)
    file2, _ = await get_looker_studio_screenshot(LOOKER_STUDIO_PILATEN_URL, "auto_pilaten.png")
    if file2 and os.path.exists(file2):
        await context.bot.send_photo(chat_id=TARGET_CHAT_ID, photo=open(file2, "rb"), caption=caption % "PI LATEN")
        os.remove(file2)

# === Main ===
async def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("msawsa", msawsa))
    app.add_handler(CommandHandler("pilaten", pilaten))
    app.add_handler(CallbackQueryHandler(section_callback))

    await app.bot.set_my_commands([
        ("start", "Tampilkan menu utama"),
        ("msawsa", "Laporan MSA/WSA"),
        ("pilaten", "Laporan PI LATEN")
    ] + [(cmd, f"Laporan {SECTION_LABELS[cmd]}") for cmd in SECTION_COORDINATES])

    app.job_queue.run_daily(send_all_snapshots, time=dt_time(10, 0, tzinfo=TIMEZONE))
    app.job_queue.run_daily(send_all_snapshots, time=dt_time(17, 0, tzinfo=TIMEZONE))

    logger.info("Bot aktif dan siap.")
    await app.run_polling()

if __name__ == '__main__':
    if os.name == "nt":
        try:
            import nest_asyncio
            nest_asyncio.apply()
        except ImportError:
            print("💡 Jalankan 'pip install nest_asyncio'")
    asyncio.run(main())
