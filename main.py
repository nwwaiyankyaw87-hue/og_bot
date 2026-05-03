import json
import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

BOT_TOKEN = "7024498547:AAFvqh3H7eePD-XvQNfu2Yr1TkwDrmsjfLc"

BRANDS = ["iPhone", "Samsung", "OPPO", "VIVO", "Redmi", "Realme", "Infinix", "TECNO", "Honor", "Huawei"]

def norm(text):
    text = str(text).lower()
    text = text.replace("iphone", "ip")
    text = text.replace("pro max", "promax")
    text = text.replace(" ", "")
    return re.sub(r"[^a-z0-9]", "", text)

def detect_brand(model):
    t = model.upper()
    if "IPHONE" in t or t.startswith("IP "): return "iPhone"
    if "SAMSUNG" in t or t.startswith("SAM "): return "Samsung"
    if "OPPO" in t: return "OPPO"
    if "VIVO" in t or t.startswith("VI "): return "VIVO"
    if "REDMI" in t or "XIAOMI" in t: return "Redmi"
    if "REALME" in t or t.startswith("RM "): return "Realme"
    if "INFINIX" in t: return "Infinix"
    if "TECNO" in t: return "TECNO"
    if "HONOR" in t: return "Honor"
    if "HUAWEI" in t: return "Huawei"
    return "Other"

def detect_series(model, brand):
    t = model.upper()
    nums = re.findall(r"\b\d{1,2}\b", t)

    if brand == "iPhone":
        return nums[0] if nums else "Other"

    if brand == "Samsung":
        m = re.search(r"\b([AMS])\s?\d+", t)
        return f"{m.group(1)} Series" if m else "Other"

    if brand in ["OPPO", "VIVO", "Redmi", "Realme"]:
        m = re.search(r"\b([A-Z]+)\s?\d+", t)
        return f"{m.group(1)} Series" if m else "Other"

    return "Other"

with open("database.json", "r", encoding="utf-8") as f:
    raw = json.load(f)

db = raw.get("database", raw)

ITEMS = []
seen = set()

for key, value in db.items():
    results = value.get("results", []) if isinstance(value, dict) else []
    aliases = value.get("aliases", []) if isinstance(value, dict) else []

    for r in results:
        model = r.get("model_original", key)
        code = r.get("code", "N/A")
        unique = f"{model}|{code}"

        if unique in seen:
            continue
        seen.add(unique)

        brand = detect_brand(model)
        series = detect_series(model, brand)

        ITEMS.append({
            "model": model,
            "code": code,
            "category": r.get("category", "Original Universal"),
            "color": r.get("color", ""),
            "status": r.get("status", ""),
            "aliases": aliases,
            "brand": brand,
            "series": series,
            "search": norm(" ".join([model, code, key] + aliases))
        })

def result_text(item):
    return f"""✅ ရှာတွေ့ပါပြီ

📱 Model: {item['model']}
🛡️ OG Code: {item['code']}
📦 Type: {item['category']}
🎨 Color: {item['color']}
✅ Status: {item['status']}

ဆိုင်မှာ {item['code']} လို့ပြောပြီး ဝယ်ယူနိုင်ပါတယ်။"""

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = []
    for b in BRANDS:
        if any(i["brand"] == b for i in ITEMS):
            keyboard.append([InlineKeyboardButton(f"📱 {b}", callback_data=f"brand|{b}")])

    await update.message.reply_text(
        "📌 Brand ကိုရွေးပါ\n\nဒါမှမဟုတ် model name ကို တိုက်ရိုက်ရိုက်ရှာနိုင်ပါတယ်။",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def text_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = norm(update.message.text)

    matches = [i for i in ITEMS if q and q in i["search"]]

    if not matches:
        await update.message.reply_text(
            "❌ မတွေ့သေးပါ\n\nModel name ကို ပိုပြည့်စုံစွာ ရိုက်ပါ။\nဥပမာ - Samsung A12, Vivo Y20, iPhone 15 Pro Max",
            reply_markup=ReplyKeyboardRemove()
        )
        return

    if len(matches) == 1:
        await update.message.reply_text(result_text(matches[0]), reply_markup=ReplyKeyboardRemove())
        return

    keyboard = []
    for i, item in enumerate(matches[:10]):
        idx = ITEMS.index(item)
        keyboard.append([InlineKeyboardButton(item["model"][:45], callback_data=f"model|{idx}")])

    await update.message.reply_text(
        "🔎 အောက်က model ထဲက ရွေးပါ",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    parts = query.data.split("|")
    action = parts[0]

    if action == "brand":
        brand = parts[1]
        series_list = sorted(set(i["series"] for i in ITEMS if i["brand"] == brand))

        keyboard = [[InlineKeyboardButton(s, callback_data=f"series|{brand}|{s}")] for s in series_list]
        keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="back|brand")])

        await query.edit_message_text(
            f"📌 {brand} Series ရွေးပါ",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif action == "series":
        brand = parts[1]
        series = parts[2]

        models = [i for i in ITEMS if i["brand"] == brand and i["series"] == series]

        keyboard = []
        for item in models[:30]:
            idx = ITEMS.index(item)
            keyboard.append([InlineKeyboardButton(item["model"][:50], callback_data=f"model|{idx}")])

        keyboard.append([InlineKeyboardButton("🔙 Back", callback_data=f"brand|{brand}")])

        await query.edit_message_text(
            "📱 Model ကိုရွေးပါ",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif action == "model":
        idx = int(parts[1])
        await query.edit_message_text(result_text(ITEMS[idx]))

    elif action == "back":
        keyboard = []
        for b in BRANDS:
            if any(i["brand"] == b for i in ITEMS):
                keyboard.append([InlineKeyboardButton(f"📱 {b}", callback_data=f"brand|{b}")])

        await query.edit_message_text(
            "📌 Brand ကိုရွေးပါ",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(button))
app.add_handler(MessageHandler(filters.TEXT, text_search))

app.run_polling()
