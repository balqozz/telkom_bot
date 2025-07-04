import asyncio
from telegram import Update, InputFile
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time

# Bot config
BOT_TOKEN = '8152147538:AAH-hjZW1db5o6obJv41Skm3NRNk1xMfoTQ'
CHAT_ID = 6655121882
DASHBOARD_URL = 'https://lookerstudio.google.com/u/0/reporting/1e34ea50-6f1c-4d9f-8d8a-bc860eb9f852/page/p_sg0esh6srd?s=mgDMBANKMdg'

# Fungsi untuk ambil screenshot dari Looker Studio
def capture_dashboard_image(filename: str):
    options = Options()
    options.add_argument('--headless') 
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--window-size=1280,1024')

    # Gunakan Service untuk inisialisasi driver
    service = Service(ChromeDriverManager().install())  # ✅ Perbaikan disini
    driver = webdriver.Chrome(service=service, options=options)  # ✅ Jangan pakai executable_path

    try:
        driver.get(DASHBOARD_URL)
        time.sleep(10)  # Waktu tunggu agar halaman termuat
        driver.save_screenshot(filename)
        print(f"✅ Screenshot disimpan sebagai {filename}")
    finally:
        driver.quit()

# Handler command /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Halo! Ketik /dashboard untuk melihat KPI Telkom 2025.")

# Handler command /dashboard (manual)
async def dashboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = (
        "\U0001F4CA <b>Hai, berikut adalah KPI MSA 2025!</b>\n\n"
        "Klik tautan di bawah ini untuk melihat laporan interaktif secara lengkap:\n"
        f"<a href='{DASHBOARD_URL}'>\U0001F517 Klik di sini untuk lihat dashboard</a>\n\n"
        "Jika butuh file ringkasan, silakan cek lampiran PDF di bawah ini ya!"
    )
    await update.message.reply_text(message, parse_mode='HTML')

    # Kirim PDF
    with open("Laporan_KPI_MSA.pdf", "rb") as pdf:
        await update.message.reply_document(document=InputFile(pdf), caption="Laporan KPI MSA 2025")

    # Kirim Gambar terbaru
    capture_dashboard_image("dashboard_kpi.jpg")
    with open("dashboard_kpi.jpg", "rb") as img:
        await update.message.reply_photo(photo=InputFile(img), caption="Tampilan KPI Terbaru")

# Fungsi otomatis harian
async def send_daily_dashboard(app):
    try:
        capture_dashboard_image("dashboard_kpi.jpg")

        message = (
            "\U0001F514 <b>Update Harian: KPI MSA 2025</b>\n\n"
            "Klik link di bawah ini untuk memantau perkembangan KPI terbaru hari ini:\n"
            f"<a href='{DASHBOARD_URL}'>\U0001F517 Klik di sini untuk lihat laporan terbaru</a>\n\n"
            "Semoga harimu produktif! \U0001F4AA"
        )
        await app.bot.send_message(chat_id=CHAT_ID, text=message, parse_mode='HTML')

        with open("dashboard_kpi.jpg", "rb") as img:
            await app.bot.send_photo(chat_id=CHAT_ID, photo=InputFile(img), caption="KPI Update Terbaru")

        print("✅ Dashboard otomatis terkirim.")
    except Exception as e:
        print(f"❌ Gagal mengirim dashboard otomatis: {e}")

# Main bot
async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).read_timeout(30).connect_timeout(30).build()

    # Command handler
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("dashboard", dashboard))

    # Scheduler otomatis
    scheduler = AsyncIOScheduler(timezone="Asia/Jakarta")
    scheduler.add_job(send_daily_dashboard, "cron", hour=9, minute=10, args=[app])
    scheduler.start()

    print("✅ Bot berjalan... Tekan Ctrl+C untuk keluar.")
    await app.run_polling()

if __name__ == "__main__":
    import nest_asyncio
    nest_asyncio.apply()
    asyncio.get_event_loop().run_until_complete(main())
