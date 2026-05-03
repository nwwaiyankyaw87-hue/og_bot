import json
import re
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

BOT_TOKEN = "7024498547:AAFvqh3H7eePD-XvQNfu2Yr1TkwDrmsjfLc"

def normalize(text):
    text = text.lower()
    text = text.replace("iphone", "ip")
    text = text.replace("pro max", "pm")
    text = text.replace(" ", "")
    return re.sub(r"[^a-z0-9]", "", text)

with open("database.json", "r", encoding="utf-8") as f:
    raw = json.load(f)

data = raw.get("database", raw)

ITEMS = []

for key, value in data.items():
    results = value.get("results", [])
    for r in results:
        model = r.get("model_original", key)
        code = r.get("code", "")

        ITEMS.append({
            "model": model,
            "code": code,
            "search": normalize(model + " " + key)
        })

async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = normalize(update.message.text)

    for item in ITEMS:
        if user_input in item["search"]:
            reply = f"""✅ တွေ့ပါတယ်

📱 Model: {item['model']}
🔑 OG Code: {item['code']}"""
            await update.message.reply_text(reply)
            return

    await update.message.reply_text("❌ မတွေ့ပါ")

app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(MessageHandler(filters.TEXT, handle))
app.run_polling()
