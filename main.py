import json
from telegram import Update, ReplyKeyboardRemove
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

with open("database.json", "r", encoding="utf-8") as f:
    data = json.load(f)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text.lower().strip()

    found = None
    matched_model = None

    for key, value in data.items():
        key_text = key.lower().strip()

        if user_input == key_text or user_input in key_text:
            found = value
            matched_model = key
            break

    if found:
        reply = f"""✅ ရှာတွေ့ပါပြီ

📱 Model: {matched_model}
🛡️ OG Code: {found}

ဆိုင်မှာ {found} လို့ပြောပြီး ဝယ်ယူနိုင်ပါတယ်။
"""
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
