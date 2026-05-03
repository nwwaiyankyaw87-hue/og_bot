import json
import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, MessageHandler, CallbackQueryHandler, filters, ContextTypes

BOT_TOKEN = "7024498547:AAFvqh3H7eePD-XvQNfu2Yr1TkwDrmsjfLc"

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

BRAND_PREFIXES = {
    "IP": "IPHONE",
    "IPHONE": "IPHONE",
    "SAM": "SAMSUNG",
    "OP": "OPPO",
    "VI": "VIVO",
    "R-ME": "REALME",
    "R-MI": "XIAOMI",
    "MI": "XIAOMI",
    "POCO": "POCO",
    "INFI": "INFINIX",
    "TECNO": "TECNO",
}

def split_models_with_brand(model_text):
    parts = re.split(r"[/,|]+", str(model_text))
    result = []
    current_brand = ""

    for part in parts:
        part = part.strip()
        if not part:
            continue

        words = part.split()
        prefix = words[0].upper()

        if prefix in BRAND_PREFIXES:
            current_brand = BRAND_PREFIXES[prefix]
            model = part[len(words[0]):].strip()
        else:
            model = part

        if model:
            result.append((current_brand, model))

    return result
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
        full_model = r.get("model_original", key)
        code = r.get("code", "")

        for brand, single_model in split_models_with_brand(full_model):
            search_text = " ".join([brand, single_model] + [str(a) for a in aliases])

            ITEMS.append({
                "model": single_model,
                "full_model": full_model,
                "brand": brand,
                "code": code,
                "search": normalize(search_text)
            })
def result_message(item):
    return f"""✅ တွေ့ပါတယ်

📱 Model: {item['brand']} • {item['model'].title()}
🔑 OG Code: {item['code']}"""
    
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = normalize(update.message.text)

    matches = []
    seen = set()

    for item in ITEMS:
        model_norm = normalize(item["model"])

        if q and q in model_norm:
            key = item["brand"] + item["model"] + item["code"]
            if key not in seen:
                matches.append(item)
                seen.add(key)

    if not matches:
        await update.message.reply_text("❌ မတွေ့ပါ")
        return

    if len(matches) == 1:
        await update.message.reply_text(result_message(matches[0]))
        return

    keyboard = []
    for item in matches[:20]:
        idx = ITEMS.index(item)
        keyboard.append([
          InlineKeyboardButton(f"{item['brand'].upper()} • {item['model'].title()}"[:50], callback_data=f"select|{idx}")
        ])

    await update.message.reply_text(
        "တူတဲ့ Model များတွေ့ပါတယ်။ ဘယ် model လဲ ရွေးပါ။",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def handle_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    _, idx = query.data.split("|")
    item = ITEMS[int(idx)]

    await query.edit_message_text(result_message(item))

app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(MessageHandler(filters.TEXT, handle_text))
app.add_handler(CallbackQueryHandler(handle_button))

app.run_polling()
