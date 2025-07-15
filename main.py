import os
import logging
import pytz
import asyncio
from dotenv import load_dotenv
from datetime import time as dt_time, datetime
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler
from playwright.async_api import async_playwright
from PIL import Image

# --- Konfigurasi ---
# --- Load environment variables ---
load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
TARGET_CHAT_ID = os.getenv("TARGET_CHAT_ID")
LOOKER_STUDIO_MSA_WSA_URL = os.getenv("LOOKER_STUDIO_MSA_WSA_URL") 
LOOKER_STUDIO_PILATEN_URL = os.getenv("LOOKER_STUDIO_PILATEN_URL")

TIMEZONE = pytz.timezone("Asia/Jakarta")

# --- Logging ---
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- Screenshot ---
async def get_looker_studio_screenshot(looker_studio_url: str, output_filename: str) -> tuple[str | None, str | None]:
    update_date_str = None
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(viewport={"width": 1500, "height": 1500})
            page = await context.new_page()

            await page.goto(looker_studio_url, timeout=60000)
            await page.wait_for_timeout(7000)
            await page.evaluate("() => { window.scrollTo(0, document.body.scrollHeight); }")
            await page.wait_for_timeout(1000)

            # Coba ekstrak tanggal update
            try:
                update_msg_span = await page.query_selector("span.updateMsg")
                if update_msg_span:
                    full_text = await update_msg_span.inner_text()
                    if "Data Terakhir Diperbarui:" in full_text:
                        update_date_str = full_text.split("Data Terakhir Diperbarui:")[1].strip()
                        logger.info(f"Tanggal update ditemukan: {update_date_str}")
            except Exception as e:
                logger.warning(f"Tidak dapat mengekstrak tanggal update dari halaman: {e}")

            align_holder = await page.query_selector("div.alignHolder")
            if align_holder:
                await align_holder.screenshot(path=output_filename)
                return output_filename, update_date_str
            else:
                logger.warning("⚠️ Elemen div.alignHolder tidak ditemukan. Mengambil screenshot seluruh halaman sebagai fallback.")
                await page.screenshot(path=output_filename, full_page=True)
                return output_filename, update_date_str
    except Exception as e:
        logger.error(f"Gagal mengambil screenshot: {e}")
        return None, None

# --- Koordinat Crop Section ---
SECTION_COORDINATES = {
    "FULL_DASHBOARD": (10, 10, 1234, 974), 
    "FULFILLMENT_FBB": (34, 36, 334, 293), 
    "ASSURANCE_FBB": (351, 114, 724, 453), 
    "SCORE_CREDIT": (772, 117, 1222, 267), 
    "FULFILLMENT_BGES": (34, 301, 333, 551), 
    "ASSURANCE_BGES": (34, 559, 333, 913), 
    "MSA_ASSURANCE": (743, 268, 1219, 622), 
    "MSA_CNOP": (349, 458, 722, 911), 
    "MSA_QUALITY": (743, 635, 1212, 911) 
}

# --- Start ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Selamat datang! Silakan pilih menu berikut untuk melihat laporan yang tersedia:\n"
        "/msawsa - Laporan MSA/WSA\n"
        "/pilaten - Laporan PI LATEN"
    )

# --- Command MSA/WSA ---
async def msawsa(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Sedang mengambil laporan MSA/WSA, harap tunggu...")

    filename = "msawsa_base_screenshot.png"
    path, _ = await get_looker_studio_screenshot(LOOKER_STUDIO_MSA_WSA_URL, filename) # Tidak menggunakan update_date di sini

    if path and os.path.exists(path):
        # Untuk command /msawsa, kirimkan dulu full dashboard
        full_dashboard_crop_box = SECTION_COORDINATES.get("FULL_DASHBOARD")
        if full_dashboard_crop_box:
            try:
                with Image.open(path) as img:
                    cropped_full = img.crop(full_dashboard_crop_box)
                    cropped_full_filename = "FULL_DASHBOARD.png"
                    cropped_full.save(cropped_full_filename)
                    with open(cropped_full_filename, "rb") as f:
                        await update.message.reply_photo(f, caption="Laporan Lengkap MSA/WSA")
                    os.remove(cropped_full_filename)
            except Exception as e:
                logger.error(f"Gagal crop full dashboard: {e}")
                await update.message.reply_text("Gagal memproses laporan lengkap MSA/WSA.")
        else:
            await update.message.reply_text("Koordinat FULL_DASHBOARD tidak ditemukan.")
        
        # Kemudian kirim tombol-tombol section
        await send_section_buttons(update.message.chat_id, context)
        
        # Hapus file screenshot dasar setelah digunakan untuk /msawsa
        if os.path.exists(path):
            os.remove(path)
    else:
        await update.message.reply_text("Gagal mengambil laporan MSA/WSA.")


# --- Fungsi untuk Kirim Tombol Section ---
async def send_section_buttons(chat_id: int, context: ContextTypes.DEFAULT_TYPE):
    section_buttons = []

    # Tombol tunggal di paling atas: FULL_DASHBOARD
    section_buttons.append([
        InlineKeyboardButton("FULL DASHBOARD", callback_data="FULL_DASHBOARD")
    ])

    # Section lainnya dalam 2 kolom, kecuali FULL_DASHBOARD
    keys = [key for key in SECTION_COORDINATES if key != "FULL_DASHBOARD"]
    for i in range(0, len(keys), 2):
        row = []
        for j in range(2):
            if i + j < len(keys):
                label = keys[i + j].replace("_", " ")
                row.append(InlineKeyboardButton(label, callback_data=keys[i + j]))
        section_buttons.append(row)

    reply_markup = InlineKeyboardMarkup(section_buttons)
    await context.bot.send_message(chat_id=chat_id, text="Silakan pilih bagian laporan yang ingin ditampilkan:", reply_markup=reply_markup)

# --- Callback Section Crop ---
async def handle_section_crop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    section = query.data
    crop_box = SECTION_COORDINATES.get(section)
    filename = "msawsa_base_screenshot.png"
    cropped_filename = f"{section}.png"

    await query.edit_message_text(
        text=f"Mengambil bagian laporan: {section.replace('_', ' ')}"
    )

    path, _ = await get_looker_studio_screenshot(LOOKER_STUDIO_MSA_WSA_URL, filename) # Tidak menggunakan update_date di sini

    if path and os.path.exists(path):
        try:
            with Image.open(path) as img:
                if crop_box:
                    # Pastikan koordinat crop tidak melebihi dimensi gambar
                    img_width, img_height = img.size
                    x1, y1, x2, y2 = crop_box
                    if x2 > img_width or y2 > img_height:
                        logger.warning(f"Koordinat crop ({crop_box}) melebihi dimensi gambar ({img_width}, {img_height}). Menyesuaikan batas.")
                        x2 = min(x2, img_width)
                        y2 = min(y2, img_height)
                        crop_box = (x1, y1, x2, y2)

                    cropped = img.crop(crop_box)
                    cropped.save(cropped_filename)
                    with open(cropped_filename, "rb") as f:
                        await context.bot.send_photo(
                            chat_id=query.message.chat_id,
                            photo=f,
                            caption=f"Laporan: {section.replace('_', ' ')}"
                        )
                    os.remove(cropped_filename)
                else:
                    logger.error(f"Gambar tidak ditemukan untuk section: {section}")
                    await context.bot.send_message(chat_id=query.message.chat_id, text="Gambar tidak ditemukan.")

        except Exception as e:
            logger.error(f"Crop error: {e}")
            await context.bot.send_message(chat_id=query.message.chat_id, text="Gagal memotong gambar.")
        finally:
            # Selalu hapus file screenshot dasar setelah digunakan
            if os.path.exists(path):
                os.remove(path)

        await send_section_buttons(query.message.chat_id, context)
    else:
        await context.bot.send_message(chat_id=query.message.chat_id, text="Gagal mengambil screenshot.")

# --- Command Pilaten ---
async def pilaten(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Sedang mengambil laporan PI LATEN, harap tunggu...")

    filename = "pilaten_base_screenshot.png"
    path, _ = await get_looker_studio_screenshot(LOOKER_STUDIO_PILATEN_URL, filename) # Tidak menggunakan update_date di sini

    if path and os.path.exists(path):
        with open(path, "rb") as f:
            await update.message.reply_photo(f, caption="Laporan Lengkap PI LATEN")
        os.remove(path)
    else:
        await update.message.reply_text("Gagal mengambil laporan PI LATEN.")

# --- Fungsi untuk mendapatkan sapaan dan waktu yang diformat ---
def get_formatted_greeting_with_time():
    current_dt = datetime.now(TIMEZONE)
    
    # Mapping nama bulan dalam Bahasa Indonesia
    month_names_id = {
        1: "Januari", 2: "Februari", 3: "Maret", 4: "April", 5: "Mei", 6: "Juni",
        7: "Juli", 8: "Agustus", 9: "September", 10: "Oktober", 11: "November", 12: "Desember"
    }
    
    # Format tanggal dan waktu sesuai keinginan: "09 Juli 2025, 11:18 WIB"
    formatted_date_time = current_dt.strftime(f"%d {month_names_id[current_dt.month]} %Y, %H:%M WIB")

    greeting_phrase = ""
    if 5 <= current_dt.hour < 12:
        greeting_phrase = "Selamat pagi"
    # elif 12 <= current_dt.hour < 18:
    #     greeting_phrase = "Selamat siang"
    else:
        greeting_phrase = "Selamat malam"
    
    # Mengembalikan string format yang akan diisi dengan jenis laporan
    return f"{greeting_phrase}, berikut laporan %s terbaru pada {formatted_date_time}"

# --- Kirim Snapshot Otomatis ---
async def send_all_snapshots(context: ContextTypes.DEFAULT_TYPE):
    # Dapatkan template caption dengan tanggal dan waktu saat ini
    caption_template = get_formatted_greeting_with_time()

    # MSA/WSA Snapshot
    # Tanggal update dari Looker Studio tidak digunakan untuk caption otomatis
    path1, _ = await get_looker_studio_screenshot(LOOKER_STUDIO_MSA_WSA_URL, "auto_msawsa_base_screenshot.png")
    if path1 and os.path.exists(path1):
        # Isi template dengan jenis laporan MSA/WSA
        caption_msa = caption_template % "MSA/WSA"
        with open(path1, "rb") as f:
            await context.bot.send_photo(chat_id=TARGET_CHAT_ID, photo=f, caption=caption_msa)
        os.remove(path1)
    else:
        logger.error("Gagal mengirim laporan MSA/WSA otomatis")

    await asyncio.sleep(5)

    # PI LATEN Snapshot
    # Tanggal update dari Looker Studio tidak digunakan untuk caption otomatis
    path2, _ = await get_looker_studio_screenshot(LOOKER_STUDIO_PILATEN_URL, "auto_pilaten_base_screenshot.png")
    if path2 and os.path.exists(path2):
        # Isi template dengan jenis laporan PI LATEN
        caption_pilaten = caption_template % "PI LATEN"
        with open(path2, "rb") as f:
            await context.bot.send_photo(chat_id=TARGET_CHAT_ID, photo=f, caption=caption_pilaten)
        os.remove(path2)
    else:
        logger.error("Gagal mengirim laporan PI LATEN otomatis")

# --- Main ---
# --- Main ---
async def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("msawsa", msawsa))
    app.add_handler(CommandHandler("pilaten", pilaten))
    app.add_handler(CallbackQueryHandler(handle_section_crop))

    job_queue = app.job_queue
    job_queue.run_daily(send_all_snapshots, time=dt_time(9, 0, tzinfo=TIMEZONE))
    job_queue.run_daily(send_all_snapshots, time=dt_time(21, 0, tzinfo=TIMEZONE))

    logger.info("Bot aktif dan siap.")
    await app.run_polling()

if __name__ == '__main__':
    import asyncio
    import sys

    # Apply nest_asyncio only on Windows local
    if sys.platform == "win32":
        try:
            import nest_asyncio
            nest_asyncio.apply()
        except ImportError:
            print("💡 Jalankan 'pip install nest_asyncio' agar bot bisa berjalan di Windows.")

    asyncio.run(main())