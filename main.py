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

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    user_name = update.effective_user.first_name
    text = update.message.text

    # Admin မဟုတ်လျှင် ဆိုင်အချက်အလက် စစ်ဆေးမည့်အပိုင်း
    if int(user_id) != ADMIN_ID and (user_id not in ALLOWED_USERS or ALLOWED_USERS[user_id].get("status") != "approved"):
        lines = [line.strip() for line in text.strip().split("\n") if line.strip()]
        
        if len(lines) >= 3:
            shop_name = lines[0]
            township = lines[1]
            viber_no = lines[2]
            
            username = f"@{update.effective_user.username}" if update.effective_user.username else "မရှိပါ"
            
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
                    InlineKeyboardButton("✅ ขွင့်ပြုမည်", callback_data=f"approve_{user_id}"),
                    InlineKeyboardButton("❌ ငြင်းပယ်မည်", callback_data=f"reject_{user_id}")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await context.bot.send_message(chat_id=ADMIN_ID, text=admin_text, reply_markup=reply_markup)
            await update.message.reply_text("⏳ သင့်ဆိုင်အတွက် ခွင့်ပြုချက်တောင်းဆိုမှုအား Admin မှ စိစစ်နေပါသည် ခဏစောင့်ဆိုင်းပေးပါဦးဗျာ။")
            
        else:
            await update.message.reply_text(
                "⚠️ ကျေးဇူးပြု၍ ပြထားသည့်အတိုင်း -\n\n"
                "ဆိုင်နာမည်\n"
                "မြို့နယ်\n"
                "(ဝယ်ယူနေကျ) Viber No.\n\n"
                "တို့ကို တစ်ကြောင်းချင်းစီ အောက်ဆင်းပြီး သေချာစွာ ရိုက်ထည့်ပေးပါခဗျာ။"
            )
        return

    # ================================================================
    # ✅ [အမှန်ကန်ဆုံး ပြင်ဆင်ချက်] ITEMS ကို သုံးပြီး Model ရှာဖွေပေးသည့်အပိုင်း
    # ================================================================
    query_clean = normalize(text)
    results = []

    # မူလစနစ်မှန်အတိုင်း အပေါ်မှာ အဆင်သင့် ဖွဲ့စည်းထားသော ITEMS List ထဲတွင် လိုက်ရှာခြင်း
    for item in ITEMS:
        if query_clean in item["search"]:
            results.append(result_message(item))

    # ရှာဖွေမှု ရလဒ်များ ပြန်လည်ပေးပို့ခြင်း
    if results:
        # ရလဒ်များကို စနစ်တကျ ခွဲခြားပြီး ပို့ပေးမည်
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
    
    data = query.data
    user_id = str(query.from_user.id)
    
    # ဆိုင်ရှင်များကို အတည်ပြုခြင်း (Approve) နှင့် ငြင်းပယ်ခြင်း (Reject) လုပ်ငန်းစဉ်များ
    if int(user_id) == ADMIN_ID:
        if data.startswith("approve_"):
            target_id = data.replace("approve_", "")
            
            # JSON ထဲတွင် status အား approved ပြောင်းလဲသိမ်းဆည်းခြင်း
            if target_id not in ALLOWED_USERS:
                ALLOWED_USERS[target_id] = {}
            ALLOWED_USERS[target_id]["status"] = "approved"
            save_allowed_users(ALLOWED_USERS)
            
            await query.edit_message_text(text=f"✅ User ID: {target_id} အား ဗော့တ်သုံးခွင့် ပြုလိုက်ပါပြီ။")
            await context.bot.send_message(chat_id=int(target_id), text="🎉 မင်္ဂလာပါဗျာ။ Admin မှ လူကြီးမင်းအား ဗော့တ်အသုံးပြုခွင့် ပေးလိုက်ပါပြီ။ ယခုမှစ၍ ဖုန်းမော်ဒယ်များကို စတင်ရိုက်နှိပ်ရှာဖွေနိုင်ပါပြီခင်ဗျာ။")
            
        elif data.startswith("reject_"):
            target_id = data.replace("reject_", "")
            
            if target_id not in ALLOWED_USERS:
                ALLOWED_USERS[target_id] = {}
            ALLOWED_USERS[target_id]["status"] = "rejected"
            save_allowed_users(ALLOWED_USERS)
            
            await query.edit_message_text(text=f"❌ User ID: {target_id} အား ငြင်းပယ်လိုက်ပါပြီ။")
            await context.bot.send_message(chat_id=int(target_id), text="⚠️ စိတ်မရှိပါနဲ့ခင်ဗျာ။ လူကြီးမင်း၏ တောင်းဆိုမှုအား Admin မှ ငြင်းပယ်လိုက်ပါသည်။")


def main():
    # ရေးထားသော Bot Token အား ပတ်ဝန်းကျင်ကနေ ဖတ်ယူခြင်း
    TOKEN = os.getenv("TELEGRAM_TOKEN")
    if not TOKEN:
        print("Error: TELEGRAM_TOKEN environment variable is not set.")
        return

    # global database object အား တင်ဆက်ခြင်း
    global database_data
    try:
        with open("database.json", "r", encoding="utf-8") as f:
            database_data = json.load(f)
    except Exception as e:
        print(f"Error loading database.json: {e}")
        database_data = {}

    app = ApplicationBuilder().token(TOKEN).build()

    # Command နှင့် Message Handler များ ထည့်သွင်းခြင်း
    from telegram.ext import CommandHandler
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(CallbackQueryHandler(callback_query_handler))

    print("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    # python-telegram-bot v20+ အတွက် စစ်ဆေးချက်များ ပြုလုပ်ရန် filters တင်သွင်းခြင်း
    from telegram.ext import filters
    main()
