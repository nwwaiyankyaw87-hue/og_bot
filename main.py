from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, MessageHandler, CallbackQueryHandler, filters, ContextTypes
import json
import re

BOT_TOKEN = "7024498547:AAFvqh3H7eePD-XvQNfu2Yr1TkwDrmsjfLc"

def normalize(text):
    text = str(text).lower()
    text = text.replace("iphone", "ip")
    text = text.replace("pro max", "pm")
    text = text.replace(" ", "")
    return re.sub(r"[^a-z0-9]", "", text)

with open("database.json", "r", encoding="utf-8") as f:
    raw = json.load(f)

data = raw.get("database", raw)

ITEMS = []

for key, value in data.items():
    results = value.get("results", []) if isinstance(value, dict) else []

    for r in results:
        model = r.get("model_original", key)
        code = r.get("code", "")

        ITEMS.append({
            "model": model,
            "code": code,
            "search": normalize(model + " " + key)
        })

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = normalize(update.message.text)

    matches = [item for item in ITEMS if q and q in item["search"]]

    if not matches:
        await update.message.reply_text("❌ မတွေ့ပါ")
        return

    if len(matches) == 1:
        item = matches[0]
        await update.message.reply_text(f"""✅ တွေ့ပါတယ်

🔑 OG Code: {item['code']}""")
        return

    keyboard = []
    for i, item in enumerate(matches[:10]):
        idx = ITEMS.index(item)
        keyboard.append([
            InlineKeyboardButton(item["model"], callback_data=f"select_{idx}")
        ])

    await update.message.reply_text(
        "တူတဲ့ model များတွေ့ပါတယ်။ ဘယ် model လဲ ရွေးပါ။",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def handle_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    idx = int(query.data.replace("select_", ""))
    item = ITEMS[idx]

    await query.edit_message_text(f"""✅ တွေ့ပါတယ်

🔑 OG Code: {item['code']}""")

app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(MessageHandler(filters.TEXT, handle_text))
app.add_handler(CallbackQueryHandler(handle_button))

app.run_polling()    

for item in ITEMS:
        if user_input in item["search"]:
            reply = f"""✅ တွေ့ပါတယ်

🔑 OG Code: {item['code']}"""
            await update.message.reply_text(reply)
            return

    await update.message.reply_text("❌ မတွေ့ပါ")

app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(MessageHandler(filters.TEXT, handle))
app.run_polling()
