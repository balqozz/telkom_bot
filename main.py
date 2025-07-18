import os
import asyncio
from datetime import time as dt_time
from telegram.ext import Application, ApplicationBuilder, CommandHandler
from config import TOKEN, TIMEZONE, logger
from handlers import start, msawsa, pilaten, send_all_snapshots

async def main():
    app = ApplicationBuilder().token(TOKEN).build()

    # Handler perintah
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("msawsa", msawsa))
    app.add_handler(CommandHandler("pilaten", pilaten))

    # Atur menu command di bot
    await app.bot.set_my_commands([
        ("start", "Tampilkan menu utama"),
        ("msawsa", "Laporan MSA/WSA"),
        ("pilaten", "Laporan PI LATEN")
    ])

    # Jadwal kirim otomatis
    app.job_queue.run_daily(send_all_snapshots, time=dt_time(10, 0, tzinfo=TIMEZONE))
    app.job_queue.run_daily(send_all_snapshots, time=dt_time(17, 0, tzinfo=TIMEZONE))

    logger.info("🤖 Bot aktif dan siap.")
    await app.run_polling()

if __name__ == '__main__':
    if os.name == "nt":
        try:
            import nest_asyncio
            nest_asyncio.apply()
        except ImportError:
            print("💡 Jalankan 'pip install nest_asyncio'")
    asyncio.run(main())
