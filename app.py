import os
from fastapi import FastAPI, Request
from dotenv import load_dotenv
import google.generativeai as genai
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

load_dotenv(".env")  # لوکال؛ روی Render از ENV vars می‌خونیم

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
MODEL_NAME = os.getenv("MODEL_NAME", "gemini-1.5-flash").strip()

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel(MODEL_NAME)

app = FastAPI()
tg_app = Application.builder().token(TELEGRAM_TOKEN).build()

async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("سلام! آنلاینم 😄")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (update.message.text or "").strip()
    if not text:
        return
    try:
        resp = model.generate_content(text)
        answer = (resp.text or "").strip() or "پاسخی برنگشت."
        await update.message.reply_text(answer[:4000])
    except Exception as e:
        await update.message.reply_text(f"Gemini error: {e}")

tg_app.add_handler(CommandHandler("start", start_cmd))
tg_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

@app.on_event("startup")
async def on_startup():
    await tg_app.initialize()
    await tg_app.start()

    # Render URL رو بعد از Deploy می‌ذاری تو ENV به اسم PUBLIC_URL
    public_url = os.getenv("PUBLIC_URL", "").rstrip("/")
    if public_url:
        await tg_app.bot.set_webhook(f"{public_url}/webhook")

@app.on_event("shutdown")
async def on_shutdown():
    await tg_app.stop()
    await tg_app.shutdown()

@app.post("/webhook")
async def telegram_webhook(req: Request):
    data = await req.json()
    update = Update.de_json(data, tg_app.bot)
    await tg_app.process_update(update)
    return {"ok": True}

@app.get("/")
def health():
    return {"status": "ok"}
