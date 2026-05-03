import json
import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, MessageHandler, CallbackQueryHandler, filters, ContextTypes

BOT_TOKEN = "7024498547:AAFvqh3H7eePD-XvQNfu2Yr1TkwDrmsjfLc"

# ---------- Normalize ----------
def normalize(text):
    text = str(text).lower()

    text = text.replace("iphone", "ip")
    text = text.replace("pro max", "promax")
    text = text.replace("pro-max", "promax")

    text = text.replace("samsung", "sam")
    text = text.replace("oppo", "op")
    text = text.replace("vivo", "vi")

    text = text.replace(" ", "")
    return re.sub(r"[^a-z0-9]", "", text)

# ---------- Load Database ----------
with open("database.json", "r", encoding="utf-8") as f:
    raw = json.load(f)

data = raw.get("database", raw)

ITEMS = []

for key, value in data.items():
    if not isinstance(value, dict):
        continue

    aliases = value.get("aliases", [])
    results = value.get("results", [])

    for r in results:
        model = r.get("model_original", key)
        code = r.get("code", "")

        search_text = " ".join([str(key), str(model), str(code)] + [str(a) for a in aliases])

        ITEMS.append({
            "model": model,
            "code": code,
            "search": normalize(search_text)
        })

# ---------- Output ----------
def result_message(item):
    return f"""✅ တွေ့ပါတယ်

📱 Model: {item["model"]}
🔑 OG Code: {item["code"]}"""

# ---------- Handle Text ----------
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = normalize(update.message.text)

    matches = []
    seen = set()

    for item in ITEMS:
        if q and q in item["search"]:
            key = item["model"] + item["code"]
            if key not in seen:
                matches.append(item)
                seen.add(key)

    if not matches:
        await update.message.reply_text("❌ မတွေ့ပါ")
        return

    # 👉 One result → show directly
    if len(matches) == 1:
        await update.message.reply_text(result_message(matches[0]))
        return

    # 👉 Multiple → show buttons
    keyboard = []
    for item in matches[:20]:
        idx = ITEMS.index(item)
        keyboard.append([
            InlineKeyboardButton(item["model"][:50], callback_data=f"select|{idx}")
        ])

    await update.message.reply_text(
        "တူတဲ့ Model များတွေ့ပါတယ်။ ဘယ် model လဲ ရွေးပါ။",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ---------- Handle Button ----------
async def handle_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    _, idx = query.data.split("|")
    item = ITEMS[int(idx)]

    await query.edit_message_text(result_message(item))

# ---------- Run Bot ----------
app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(MessageHandler(filters.TEXT, handle_text))
app.add_handler(CallbackQueryHandler(handle_button))

app.run_polling()
