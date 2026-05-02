import json
from telegram import Update, ReplyKeyboardRemove
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

BOT_TOKEN = "ဒီနေရာမှာ BotFather token ထည့်ပါ"

with open("database.json", "r", encoding="utf-8") as f:
    raw_data = json.load(f)

data = raw_data.get("database", raw_data)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text.lower().strip()

    found_item = None
    matched_alias = None

    for key, value in data.items():
        key_text = str(key).lower().strip()

        if user_input == key_text or user_input in key_text:
            found_item = value
            matched_alias = key
            break

    if found_item:
        result = found_item["results"][0]

        code = result.get("code", "N/A")
        model = result.get("model_original", matched_alias)
        category = result.get("category", "Original Universal")
        color = result.get("color", "")
        status = result.get("status", "")

        reply = f"""✅ ရှာတွေ့ပါပြီ

📱 Model: {model}
🛡️ OG Code: {code}
📦 Type: {category}
🎨 Color: {color}
✅ Status: {status}

ဆိုင်မှာ {code} လို့ပြောပြီး ဝယ်ယူနိုင်ပါတယ်။"""
    else:
        reply = """❌ မတွေ့သေးပါ

Model name ကို ပိုပြည့်စုံစွာ ရိုက်ပါ။
ဥပမာ - Samsung A12, Vivo Y20, Redmi Note 10"""

    await update.message.reply_text(
        reply,
        reply_markup=ReplyKeyboardRemove()
    )

app = ApplicationBuilder().token("7024498547:AAHrAySQkINsOCKK4QWh6vZDTQ3KBgU-Sow").build()
app.add_handler(MessageHandler(filters.TEXT, handle_message))
app.run_polling()
