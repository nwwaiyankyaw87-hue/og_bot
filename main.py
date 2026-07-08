import os
import json
import re
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, MessageHandler, CallbackQueryHandler, filters, ContextTypes

# .env file ကို load လုပ်ခြင်း
load_dotenv()

ADMIN_ID = int(os.getenv("ADMIN_ID", "0").strip()) 
USERS_FILE = "allowed_users.json"

def load_allowed_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_allowed_users(users_data):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users_data, f, ensure_ascii=False, indent=4)

ALLOWED_USERS = load_allowed_users()

# Token ကို environment variable ထဲကနေ လှမ်းယူခြင်း
BOT_TOKEN = os.getenv("TELEGRAM_TOKEN")

# ================================================================
# 🎯 အစ်ကို့ရဲ့ မူလ normalize (လုံးဝ မပြောင်းလဲထားပါ)
# ================================================================
def normalize(text):
    text = str(text).lower()
    text = text.replace("iphone", "ip")
    text = text.replace("pro max", "promax")
    text = text.replace("pro-max", "promax")
    text = text.replace("samsung", "sam")
    text = text.replace("oppo", "op")
    text = text.replace("vivo", "vi")
    text = text.replace("redmi", "rm")
    text = text.replace("realme", "rme")
    text = text.replace(" ", "")
    return re.sub(r"[^a-z0-9]", "", text)

BRAND_PREFIXES = {
    "IP": "IPHONE",
    "IPHONE": "IPHONE",
    "SAM": "SAMSUNG",
    "SAMSUNG": "SAMSUNG",
    "OP": "OPPO",
    "OPPO": "OPPO",
    "VI": "VIVO",
    "VIVO": "VIVO",
    "R-ME": "REALME",
    "REALME": "REALME",
    "RM": "REDMI",
    "REDMI": "REDMI",
    "MI": "XIAOMI",
    "XIAOMI": "XIAOMI",
    "POCO": "POCO",
    "INFI": "INFINIX",
    "INFINIX": "INFINIX",
    "TECNO": "TECNO",
    "1+": "OnePlus",
    "ONEPLUS": "OnePlus",
}

def split_models_with_brand(model_text):
    parts = re.split(r"[/,|]+", str(model_text))
    result = []
    current_brand = ""

    for part in parts:
        part = part.strip()
        if not part:
            continue

        matched = False
        for brand_prefix, brand_name in BRAND_PREFIXES.items():
            if part.upper().startswith(brand_prefix):
                current_brand = brand_name
                model = part[len(brand_prefix):].strip()
                matched = True
                break

        if not matched:
            model = part
            if model.upper().startswith(("SPARK", "CAMON", "POVA", "POP")):
                current_brand = "TECNO"
            elif model.upper().startswith(("HOT", "NOTE", "SMART", "ZERO")):
                current_brand = "INFINIX"
            elif model.upper().startswith(("NORD", "ACE")):
                current_brand = "ONEPLUS"
            elif model.upper().startswith(("MI", "REDMI", "POCO", "CIVI")):
                current_brand = "XIAOMI"
            elif model.upper().startswith(("G", "E", "EDGE", "MOTO")):
                current_brand = "MOTOROLA"

        if current_brand == "MOTOROLA":
            model = re.sub(r"^Moto\s+", "", model, flags=re.IGNORECASE)

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
            brand_clean = normalize(brand)
            model_clean = normalize(single_model)

            search_terms = set()
            search_terms.add(brand_clean + model_clean)
            search_terms.add(model_clean)

            for alias in aliases:
                alias_clean = normalize(alias)
                search_terms.add(alias_clean)
                search_terms.add(brand_clean + alias_clean)

            ITEMS.append({
                "model": single_model.strip(),
                "full_model": full_model,
                "brand": brand,
                "code": code,
                "search": search_terms
            })

def result_message(item):
    model_text = item['model'].replace('Moto ', '').title()
    display_brand = item['brand'].upper()
    
    if display_brand == "REDMI":
        display_brand = "RM"
    elif display_brand == "REALME":
        display_brand = "R-Me"
    else:
        display_brand = display_brand.title()

    if model_text.upper().startswith("PIXEL"):
        display_name = "Pixel • " + model_text[5:].strip()
    else:
        display_name = f"{display_brand} • {model_text}"

    return f"""✅ တွေ့ပါတယ်

📱 Model: {display_name}
🔑 OG Code: {item['code']}"""

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    user_name = update.effective_user.first_name
    text = update.message.text

    # 🔒 Admin အကောင့် သို့မဟုတ် Approved ဖြစ်ပြီးသားဆိုင်များ မဟုတ်ပါက စစ်ဆေးမည့် အပိုင်း
    if int(user_id) != ADMIN_ID and (user_id not in ALLOWED_USERS or ALLOWED_USERS[user_id].get("status") != "approved"):
        lines = [line.strip() for line in text.strip().split("\n") if line.strip()]
        
        if len(lines) >= 3:
            shop_name = lines[0]
            township = lines[1]
            viber_no = lines[2]
            
            username = f"@{update.effective_user.username}" if update.effective_user.username else "မရှိပါ"
            
            ALLOWED_USERS[user_id] = {
                "status": "pending",
                "info": f"👤 {user_name}\n🏪 {shop_name}\n📍 {township}\n📱 Viber: {viber_no}\n🏷️ Username: {username}"
            }
            save_allowed_users(ALLOWED_USERS)

            admin_text = (
                f"🚨 **ခွင့်ပြုချက်တောင်းခံလွှာသစ်**\n\n"
                f"👤 တောင်းခံသူ: {user_name}\n"
                f"🆔 Telegram ID: `{user_id}`\n"
                f"🏷️ Username: {username}\n"
                f"🏪 ဆိုင်နာမည်: {shop_name}\n"
                f"📍 မြို့နယ်: {township}\n"
                f"📱 Viber No: {viber_no}"
            )
            
            keyboard = [
                [
                    InlineKeyboardButton("✅ ခွင့်ပြုမည်", callback_data=f"allow|{user_id}"),
                    InlineKeyboardButton("❌ ငြင်းပယ်မည်", callback_data=f"block|{user_id}")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await context.bot.send_message(chat_id=ADMIN_ID, text=admin_text, reply_markup=reply_markup, parse_mode="Markdown")
            await update.message.reply_text("⏳ သင့်ဆိုင်အတွက် ခွင့်ပြုချက်တောင်းဆိုမှုအား Admin မှ စိစစ်နေပါသည် ခဏစောင့်ဆိုင်းပေးပါဦးဗျာ။")
            
        else:
            await update.message.reply_text(
                "👋 မင်္ဂလာပါခင်ဗျာ။ IT'S ME OG Glass Universal List Bot မှ ကြိုဆိုပါတယ်။\n\n"
                "⚠️ ဒီBotကို KWY's Accessories မှ OG Glass ဝယ်ယူသူများအတွက်သီးသန့် Bot လေးဖြစ်ပါတယ်။ "
                "BOT အသုံးပြုခွင့်ရရှိရန် အောက်ပါပုံစံအတိုင်း ဖြည့်ပေးပါဦးခဗျာ။\n\n"
                "ဆိုင်နာမည်\n"
                "မြို့နယ်\n"
                "(ဝယ်ယူနေကျ) Viber No.\n\n"
                "ဥပမာ -\n"
                "New Wave Mobile\n"
                "အလုံ\n"
                "09890080106"
            )
        return

    # ================================================================
    # 🔍 မူလ အစ်ကို့ရဲ့ မော်ဒယ်ရှာဖွေရေး စနစ် (အတိုင်းမပျက်)
    # ================================================================
    query_clean = normalize(text)
    results = []

    for item in ITEMS:
        if query_clean in item["search"]:
            results.append(result_message(item))

    if results:
        response_text = "\n\n====================\n\n".join(results)
        await update.message.reply_text(response_text)
    else:
        await update.message.reply_text(
            "❌ လူကြီးမင်းရှာဖွေနေသော မော်ဒယ်အား ရှာမတွေ့ပါခင်ဗျာ။\n"
            "စာလုံးပေါင်း မှန်ကန်စွာဖြင့် ထပ်မံရှာဖွေကြည့်ပေးပါဦး။"
        )

async def callback_query_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.from_user.id != ADMIN_ID:
        return

    data = query.data
    if data.startswith("allow|") or data.startswith("block|"):
        action, target_id = data.split("|")[0], data.split("|")[1]
        
        if target_id not in ALLOWED_USERS:
            await query.edit_message_text("❌ ဤအသုံးပြုသူ၏ အချက်အလက်ကို ရှာမတွေ့တော့ပါ။")
            return

        if action == "allow":
            ALLOWED_USERS[target_id]["status"] = "approved"
            save_allowed_users(ALLOWED_USERS)
            await query.edit_message_text(f"✅ အသုံးပြုခွင့်ပေးလိုက်ပါပြီ-\n{ALLOWED_USERS[target_id]['info']}")
            try:
                await context.bot.send_message(
                    chat_id=int(target_id),
                    text="🎉 မင်္ဂလာပါ! အသုံးပြုခွင့် တောင်းဆိုမှုကို Admin မှ အတည်ပြုပေးလိုက်ပါပြီ။ ယခုမှစ၍ စတင်ရှာဖွေနိုင်ပါပြီဗျာ။"
                )
            except Exception: pass

        elif action == "block":
            ALLOWED_USERS[target_id]["status"] = "rejected"
            save_allowed_users(ALLOWED_USERS)
            await query.edit_message_text(f"❌ ငြင်းပယ်/ပိတ်ပင်လိုက်ပါပြီ-\n{ALLOWED_USERS[target_id]['info']}")
            try:
                await context.bot.send_message(
                    chat_id=int(target_id),
                    text="⛔️ သင့်၏ဗော့တ်အသုံးပြုခွင့်ကို Admin မှ ငြင်းပယ်လိုက်ပါသည်။"
                )
            except Exception: pass

def main():
    TOKEN = os.getenv("TELEGRAM_TOKEN")
    if not TOKEN:
        print("Error: TELEGRAM_TOKEN environment variable is not set.")
        return

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(CallbackQueryHandler(callback_query_handler))

    print("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
