import os
import json
import re
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, MessageHandler, CallbackQueryHandler, CommandHandler, filters, ContextTypes

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
    "OP": "OPPO",
    "VI": "VIVO",
    "R-ME": "REALME",
    "R-MI": "RM",
    "MI": "XIAOMI",
    "POCO": "POCO",
    "INFI": "INFINIX",
    "TECNO": "TECNO",
    "1+": "OnePlus",
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

            # TECNO Models
            if model.upper().startswith(("SPARK", "CAMON", "POVA", "POP")):
                current_brand = "TECNO"

            # INFINIX Models
            elif model.upper().startswith(("HOT", "NOTE", "SMART", "ZERO")):
                current_brand = "INFINIX"

            # ONEPLUS Models
            elif model.upper().startswith(("NORD", "ACE")):
                current_brand = "ONEPLUS"
                
            # XIAOMI Models
            elif model.upper().startswith(("MI", "REDMI", "POCO", "CIVI")):
                current_brand = "XIAOMI"

            # MOTOROLA Models
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
            search_text = " ".join([brand, single_model] + [str(a) for a in aliases])

            ITEMS.append({
                "model": single_model,
                "full_model": full_model,
                "brand": brand,
                "code": code,
                "search": normalize(search_text)
            })
def result_message(item):

    model_text = item['model'].replace('Moto ', '').title()

    if model_text.upper().startswith("PIXEL"):
        display_name = "Pixel • " + model_text[5:].strip()
    else:
        display_name = f"{item['brand']} • {model_text}"

    return f"""✅ တွေ့ပါတယ်

📱 Model: {display_name}
🔑 OG Code: {item['code']}"""
    
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    
    if int(user_id) == ADMIN_ID or (user_id in ALLOWED_USERS and ALLOWED_USERS[user_id].get("status") == "approved"):
        await update.message.reply_text("👋 မင်္ဂလာပါ! ရှာဖွေလိုသည့် ဖုန်းမော်ဒယ်ကို ရိုက်ထည့်ပေးပါ။")
        return

    if user_id in ALLOWED_USERS and ALLOWED_USERS[user_id].get("status") == "pending":
        await update.message.reply_text("⏳ သင့်ဆိုင်အတွက် ခွင့်ပြုချက်တောင်းဆိုထားမှုအား Admin မှ စိစစ်နေဆဲဖြစ်ပါသည်။ ခေတ္တစောင့်ဆိုင်းပေးပါ။")
        return

    await update.message.reply_text(
        "👋 မင်္ဂလာပါခင်ဗျာ။ IT'S ME OG Glass Universal List Bot မှ ကြိုဆိုပါတယ်ခဗျာ။\n\n"
        "⚠️ ယခု BOT အား KWY's Accessoriesမှ OG Glass ဝယ်ယူထားသော Customerများသုံးရန်အတွက်သာ "
        "BOT အသုံးပြုခွင့်ရရန် အောက်ပါအတိုင်း Register ပြုလုပ်ပါ။ \n\n"
        "ဆိုင်နာမည်\n"
        "မြို့နယ်\n"
        "(ဝယ်ယူနေကျ) Viber No.\n\n"
        "ဥပမာ -\n"
        "New Wave Mobile\n"
        "အလုံ\n"
        "09890080106"
    )

("✅ အချက်အလက်များ ရရှိပါပြီ။ Admin မှ အတည်ပြုပေးသည်နှင့် စတင်အသုံးပြုနိုင်မည်ဖြစ်ပါသည်။")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    user_text = update.message.text.strip()

    # သုံးခွင့်ရှိ/မရှိ အရင်စစ်ဆေးခြင်း
    if int(user_id) != ADMIN_ID and (user_id not in ALLOWED_USERS or ALLOWED_USERS[user_id].get("status") != "approved"):
        if user_id not in ALLOWED_USERS or ALLOWED_USERS[user_id].get("status") == "pending":
            if "-" in user_text:
                ALLOWED_USERS[user_id] = {
                    "info": user_text,
                    "status": "pending",
                    "username": update.effective_user.username or "No Username"
                }
                save_allowed_users(ALLOWED_USERS)
                await update.message.reply_text("✅ အချက်အလက်များ ရရှိပါပြီ။ Admin မှ အတည်ပြုပေးသည်နှင့် စတင်အသုံးပြုနိုင်မည်ဖြစ်ပါသည်။")
                
                if ADMIN_ID != 0:
                    keyboard = [
                        [
                            InlineKeyboardButton("Allow ✅", callback_data=f"adm|allow|{user_id}"),
                            InlineKeyboardButton("Block ❌", callback_data=f"adm|block|{user_id}")
                        ]
                    ]
                    await context.bot.send_message(
                        chat_id=ADMIN_ID,
                        text=f"🔔 **• ဆိုင်အသစ် သုံးခွင့်တောင်းဆိုချက် •**\n\n🏪 အချက်အလက်: {user_text}\n🆔 TG ID: `{user_id}`\n👤 Username: @{ALLOWED_USERS[user_id]['username']}",
                        reply_markup=InlineKeyboardMarkup(keyboard),
                        parse_mode="Markdown"
                    )
            else:
                await update.message.reply_text("⚠️ ကျေးဇူးပြု၍ ပြထားသည့်အတိုင်း **[ ဆိုင်အမည် - ဖုန်းနံပါတ် ]** ပုံစံအတိုင်း သေချာစွာ ရိုက်ထည့်ပေးပါ။")
            return
        else:
            await update.message.reply_text("⛔️ သင့်အား ဗော့တ်အသုံးပြုခွင့် ပိတ်ပင်ထားပါသည်။")
            return


            except Exception: pass


app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start_command))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
app.add_handler(CallbackQueryHandler(handle_button))

print("Bot started...")
app.run_polling()
