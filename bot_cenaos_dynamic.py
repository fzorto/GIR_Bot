import os
from datetime import time
from zoneinfo import ZoneInfo  # En Windows: pip install tzdata
from dotenv import load_dotenv

from telegram import Update, InputMediaPhoto, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, ContextTypes, JobQueue

load_dotenv()

# --- Configuración ---
TZ = ZoneInfo("America/Tegucigalpa")
IMAGES = [
    "https://cenaos.copeco.gob.hn/productos/wrf/00/precipitacion/wrf24hrs.png",
    "https://cenaos.copeco.gob.hn/productos/wrf/00/precipitacion/wrf48hrs.png",
    "https://cenaos.copeco.gob.hn/productos/wrf/00/precipitacion/wrf72hrs.png",
]
PAGE = "https://cenaos.copeco.gob.hn/modelosnum.html"


async def send_album(chat_id: int | str, context: ContextTypes.DEFAULT_TYPE):
    media = [InputMediaPhoto(u) for u in IMAGES]
    await context.bot.send_media_group(chat_id=chat_id, media=media)
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("🌐 Ver página CENAOS", url=PAGE)]])
    await context.bot.send_message(chat_id=chat_id, text="Fuente: CENAOS-COPECO", reply_markup=kb, disable_web_page_preview=True)


# --- Comandos ---
async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Envío las imágenes del WRF (Precipitación 24h, Tmax, Tmin).\n"
        "Usa /modelos para recibirlas ahora. Publico al canal a las 14:00."
    )

async def cmd_modelos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_album(update.message.chat_id, context)

async def job_post(context: ContextTypes.DEFAULT_TYPE):
    channel = os.getenv("CHANNEL_ID")
    if channel:
        await send_album(channel, context)


# --- Arranque con programación segura ---
async def post_init(app: Application):
    # Asegurar JobQueue y programar
    if app.job_queue is None:
        jq = JobQueue()
        jq.set_application(app)
        app._job_queue = jq
        jq.start()

    # Programar a las 14:00 hora de Tegucigalpa
    app.job_queue.run_daily(job_post, time(hour=14, minute=15, tzinfo=TZ), name="post_14")


def main():
    token = os.getenv("TELEGRAM_TOKEN")
    if not token:
        raise RuntimeError("Falta TELEGRAM_TOKEN en variables de entorno.")

    app = Application.builder().token(token).post_init(post_init).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("modelos", cmd_modelos))
    app.run_polling()


if __name__ == "__main__":
    main()


