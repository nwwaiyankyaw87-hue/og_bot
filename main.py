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
        
        # Enter ခေါက်ပြီး ရိုက်ထားသည့် စာကြောင်းများကို ခွဲထုတ်ခြင်း
        lines = [line.strip() for line in text.strip().split("\n") if line.strip()]
        
        if len(lines) >= 3:
            shop_name = lines[0]
            township = lines[1]
            viber_no = lines[2]
            
            admin_text = (
                f"🚨 **ခွင့်ပြုချက်တောင်းခံလွှာသစ်**\n\n"
                f"👤 တောင်းခံသူ: {user_name} (ID: {user_id})\n"
                f"🏪 ဆိုင်နာမည်: {shop_name}\n"
                f"📍 မြို့နယ်: {township}\n"
                f"📱 Viber No: {viber_no}"
            )
            
            # ခွင့်ပြုရန်/ငြင်းပယ်ရန် ခလုတ်များ ပြုလုပ်ခြင်း
            keyboard = [
                [
                    InlineKeyboardButton("✅ ခွင့်ပြုမည်", callback_data=f"approve_{user_id}"),
                    InlineKeyboardButton("❌ ငြင်းပယ်မည်", callback_data=f"reject_{user_id}")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            # အစ်ကို့ (Admin) ဆီသို့ စာလှမ်းပို့ခြင်း
            await context.bot.send_message(chat_id=ADMIN_ID, text=admin_text, reply_markup=reply_markup)
            
            # ဆိုင်ရှင်အသစ်ထံ စာပြန်ခြင်း
            await update.message.reply_text("⏳ သင့်ဆိုင်အတွက် ခွင့်ပြုချက်တောင်းဆိုမှုအား Admin မှ စိစစ်နေပါသည် ခဏစောင့်ဆိုင်းပေးပါဦးဗျာ။")
            
        else:
            # ၃ ကြောင်း ပြည့်အောင် မရိုက်လျှင် ပြသမည့်စာ
            await update.message.reply_text(
                "⚠️ ကျေးဇူးပြု၍ ပြထားသည့်အတိုင်း -\n\n"
                "ဆိုင်နာမည်\n"
                "မြို့နယ်\n"
                "(ဝယ်ယူနေကျ) Viber No.\n\n"
                "တို့ကို တစ်ကြောင်းချင်းစီ အောက်ဆင်းပြီး သေချာစွာ ရိုက်ထည့်ပေးပါခဗျာ။"
            )
        return

 
        else:
            await update.message.reply_text("⛔️ သင့်အား ဗော့တ်အသုံးပြုခွင့် ပိတ်ပင်ထားပါသည်။")
            return


    q = normalize(user_text)
    matches = []
    seen = set()

    for item in ITEMS:
        search_norm = normalize(item["brand"] + " " + item["model"])
        key = item["brand"] + item["model"] + item["code"]

        if q in search_norm:
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
        button_model = item['model'].replace('Moto ', '').title()

        if button_model.upper().startswith("PIXEL"):
            button_text = "Pixel • " + button_model[5:].strip()
        else:
            button_text = f"{item['brand']} • {button_model}"

        keyboard.append([InlineKeyboardButton(button_text[:50], callback_data=f"select|{idx}")])

    await update.message.reply_text(
        "တူတဲ့ Model များတွေ့ပါတယ်။ ဘယ် model လဲ ရွေးပါ။",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def handle_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data.startswith("select|"):
        idx = int(data.split("|")[1])
        item = ITEMS[idx]
        await query.message.delete()
        await query.message.reply_text(result_message(item))
        return

    # Admin ခလုတ်များအတွက် ထပ်တိုးချက်
    if data.startswith("adm|"):
        if update.effective_user.id != ADMIN_ID:
            return
            
        action, target_id = data.split("|")[1], data.split("|")[2]
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
            ALLOWED_USERS[target_id]["status"] = "blocked"
            save_allowed_users(ALLOWED_USERS)
            await query.edit_message_text(f"❌ ပိတ်ပင် (Block) လိုက်ပါပြီ-\n{ALLOWED_USERS[target_id]['info']}")
            try:
                await context.bot.send_message(
                    chat_id=int(target_id),
                    text="⛔️ သင့်၏ဗော့တ်အသုံးပြုခွင့်ကို Admin မှ ငြင်းပယ်လိုက်ပါသည်။"
                )
            except Exception: pass


app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
app.add_handler(CallbackQueryHandler(handle_button))

print("Bot started...")
app.run_polling()
