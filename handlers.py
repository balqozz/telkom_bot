import os
from PIL import Image
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import ContextTypes
from config import (
    LOOKER_STUDIO_MSA_WSA_URL, LOOKER_STUDIO_PILATEN_URL, TARGET_CHAT_ID
)
from utils import get_greeting, get_formatted_greeting_with_time, get_looker_studio_screenshot
import asyncio

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [["/msawsa", "/pilaten"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)
    await update.message.reply_text(
        f"{get_greeting()}, selamat datang di Dashboard Monitoring Telkom!\n\nBerikut adalah dua laporan utama:\n/msawsa\n/pilaten",
        reply_markup=reply_markup
    )

# async def send_section_buttons(chat_id: int, context: ContextTypes.DEFAULT_TYPE):
#     keys = list(SECTION_COORDINATES.keys())
#     keys.remove("fulldashboard")
#     buttons = [
#         [
#             InlineKeyboardButton(SECTION_LABELS[keys[i]], callback_data=keys[i]),
#             InlineKeyboardButton(SECTION_LABELS[keys[i+1]], callback_data=keys[i+1])
#         ] for i in range(0, len(keys)-1, 2)
#     ]
#     if len(keys) % 2 == 1:
#         buttons.append([InlineKeyboardButton(SECTION_LABELS[keys[-1]], callback_data=keys[-1])])

#     await context.bot.send_message(
#         chat_id=chat_id,
#         text="Silakan pilih bagian laporan yang ingin ditampilkan:",
#         reply_markup=InlineKeyboardMarkup(buttons)
#     )

async def msawsa(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Tampilkan pesan sementara
    status_message = await update.message.reply_text("Sedang mengambil laporan MSA/WSA ...")

    # Ambil screenshot Looker Studio
    file, _ = await get_looker_studio_screenshot(LOOKER_STUDIO_MSA_WSA_URL, "msawsa_dashboard.png")
    if file and os.path.exists(file):
        await context.bot.send_photo(chat_id=update.effective_chat.id, photo=open(file, "rb"))
        os.remove(file)

        # Hapus pesan sebelumnya setelah gambar terkirim
        await status_message.delete()
    else:
        await status_message.edit_text("Gagal mengambil laporan MSA/WSA.")
async def pilaten(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Tampilkan pesan sementara
    status_message = await update.message.reply_text("Sedang mengambil laporan PI LATEN ...")

    # Ambil screenshot Looker Studio
    file, _ = await get_looker_studio_screenshot(LOOKER_STUDIO_PILATEN_URL, "pilaten_dashboard.png")
    if file and os.path.exists(file):
        await context.bot.send_photo(chat_id=update.effective_chat.id, photo=open(file, "rb"))
        os.remove(file)

        # Hapus pesan sebelumnya setelah gambar terkirim
        await status_message.delete()
    else:
        await status_message.edit_text("Gagal mengambil laporan PI LATEN.")

# CALLBACK SECTION
# async def section_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     query = update.callback_query
#     await query.answer()

#     key = query.data
#     if key not in SECTION_COORDINATES:
#         return await query.edit_message_text("Bagian laporan tidak dikenali.")

#     await query.edit_message_text(f"Mengambil bagian laporan: {SECTION_LABELS[key]}")

#     file, _ = await get_looker_studio_screenshot(LOOKER_STUDIO_MSA_WSA_URL, f"{key}_base.png")
#     if file and os.path.exists(file):
#         with Image.open(file) as img:
#             cropped = img.crop(SECTION_COORDINATES[key])
#             crop_name = f"{key}_cropped.png"
#             cropped.save(crop_name)

#             with open(crop_name, "rb") as photo:
#                 await context.bot.send_photo(
#                     chat_id=query.message.chat_id,
#                     photo=photo,
#                     caption=f"Laporan: {SECTION_LABELS[key]}"
#                 )

#             os.remove(crop_name)
#         os.remove(file)
#         await send_section_buttons(query.message.chat_id, context)
#     else:
#         await context.bot.send_message(chat_id=query.message.chat_id, text="Gagal mengambil screenshot.")

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
