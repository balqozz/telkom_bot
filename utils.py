import os
from datetime import datetime
import asyncio
from playwright.async_api import async_playwright
from PIL import Image
from config import TIMEZONE, logger

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