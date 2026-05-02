from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

TOKEN = "7024498547:AAHrAySQkINsOCKK4QWh6vZDTQ3KBgU-Sow"

# --- SAMPLE DATA ---
DATA = {
    "iphone": {
        "15": {
            "iPhone 15 Pro Max": "XMT-K104",
            "iPhone 15 Pro": "XMT-K105"
        },
        "16": {
            "iPhone 16 Pro": "XMT-K200"
        }
    },
    "samsung": {
        "A Series": {
            "Samsung A10": "OG-A10",
            "Samsung A12": "OG-A12"
        }
    }
}

# --- START ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🍎 iPhone", callback_data="brand_iphone")],
        [InlineKeyboardButton("📱 Samsung", callback_data="brand_samsung")]
    ]
    await update.message.reply_text(
        "📌 Brand ကိုရွေးပါ",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# --- BUTTON HANDLER ---
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data

    # -------- BRAND --------
    if data.startswith("brand_"):
        brand = data.split("_")[1]

        series_list = DATA.get(brand, {})
        keyboard = []

        for series in series_list:
            keyboard.append([InlineKeyboardButton(series, callback_data=f"series_{brand}_{series}")])

        await query.edit_message_text(
            f"📌 {brand.upper()} Series ရွေးပါ",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    # -------- SERIES --------
    elif data.startswith("series_"):
        _, brand, series = data.split("_")

        models = DATA[brand][series]
        keyboard = []

        for model in models:
            keyboard.append([InlineKeyboardButton(model, callback_data=f"model_{brand}_{series}_{model}")])

        await query.edit_message_text(
            f"📱 Model ရွေးပါ",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    # -------- MODEL --------
    elif data.startswith("model_"):
        _, brand, series, model = data.split("_", 3)

        code = DATA[brand][series][model]

        await query.edit_message_text(
            f"""✅ ရှာတွေ့ပါပြီ

📱 Model: {model}
🛡️ OG Code: {code}
📦 Type: Original Universal
🎨 Color: BLACK
✅ Status: Ready"""
        )

# --- MAIN ---
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(button))

app.run_polling()
