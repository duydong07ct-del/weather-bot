import datetime
import requests
from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
    Update,
)
from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

# Token đã được điền sẵn
BOT_TOKEN = "8833996135:AAH4yoUJ9-cApgZ0lp5JSlZd83wnP8fIZiU"

def get_weather(lat, lon, target_date_str):
    url = (
        f"https://api.open-meteo.com/v1/forecast?"
        f"latitude={lat}&longitude={lon}"
        f"&hourly=temperature_2m,precipitation_probability"
        f"&daily=temperature_2m_max,temperature_2m_min,precipitation_probability_max"
        f"&timezone=auto"
    )
    try:
        res = requests.get(url, timeout=10)
        data = res.json()
        daily = data.get("daily", {})
        dates = daily.get("time", [])

        if target_date_str not in dates:
            return "⚠️ Ngày bạn chọn không nằm trong phạm vi dự báo (tối đa 7 ngày tới)."

        d_idx = dates.index(target_date_str)
        t_max = daily["temperature_2m_max"][d_idx]
        t_min = daily["temperature_2m_min"][d_idx]
        rain_max = daily["precipitation_probability_max"][d_idx]

        hourly = data.get("hourly", {})
        rain_hours = []

        for i, time_val in enumerate(hourly.get("time", [])):
            if time_val.startswith(target_date_str):
                hour_str = time_val.split("T")[1]
                prob = hourly["precipitation_probability"][i]
                if prob >= 30:
                    rain_hours.append(f"  • {hour_str}: ~{prob}%")

        msg = [
            f"🌤 **DỰ BÁO THỜI TIẾT TẠI VỊ TRÍ CỦA BẠN**",
            f"📅 **Ngày:** {target_date_str}",
            f"🌡 **Nhiệt độ:** {t_min}°C đến {t_max}°C",
            f"🌧 **Tỉ lệ có mưa cao nhất trong ngày:** {rain_max}%",
            "----------------------------",
        ]

        if rain_hours:
            msg.append("⚠️ **CÁC THỜI ĐIỂM DỰ BÁO CÓ MƯA:**")
            msg.extend(rain_hours)
            msg.append("\n👉 *Nhớ mang theo ô hoặc áo mưa vào các khung giờ trên!*")
        else:
            msg.append("☀️ **Cả ngày khả năng mưa rất thấp, thời tiết khô ráo.**")

        return "\n".join(msg)
    except Exception:
        return "⚠️ Không thể tải dữ liệu thời tiết lúc này. Vui lòng thử lại sau."

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    btn_location = KeyboardButton("📍 Gửi vị trí hiện tại của tôi", request_location=True)
    keyboard = ReplyKeyboardMarkup([[btn_location]], resize_keyboard=True, one_time_keyboard=True)
    text = (
        "👋 Chào bạn! Tôi là bot dự báo thời tiết.\n\n"
        "Hãy bấm nút **'📍 Gửi vị trí hiện tại của tôi'** bên dưới để bot lấy tọa độ thiết bị của bạn."
    )
    await update.message.reply_text(text, reply_markup=keyboard, parse_mode="Markdown")

async def handle_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lat = update.message.location.latitude
    lon = update.message.location.longitude
    context.user_data["lat"] = lat
    context.user_data["lon"] = lon

    today = datetime.date.today()
    tomorrow = today + datetime.timedelta(days=1)
    day_after = today + datetime.timedelta(days=2)

    inline_keyboard = [
        [InlineKeyboardButton("Hôm nay", callback_data=today.strftime("%Y-%m-%d"))],
        [InlineKeyboardButton("Ngày mai", callback_data=tomorrow.strftime("%Y-%m-%d"))],
        [InlineKeyboardButton(f"Ngày {day_after.strftime('%d/%m')}", callback_data=day_after.strftime("%Y-%m-%d"))],
    ]
    reply_markup = InlineKeyboardMarkup(inline_keyboard)
    await update.message.reply_text(
        "✅ Đã nhận vị trí thiết bị thành công!\n👉 Chọn ngày bạn muốn xem dự báo thời tiết:",
        reply_markup=reply_markup,
    )

async def handle_date_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    selected_date = query.data
    lat = context.user_data.get("lat")
    lon = context.user_data.get("lon")

    if not lat or not lon:
        await query.edit_message_text("⚠️ Chưa có thông tin vị trí. Vui lòng gõ lại /start để chia sẻ định vị.")
        return

    report = get_weather(lat, lon, selected_date)
    await query.edit_message_text(report, parse_mode="Markdown")

if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.LOCATION, handle_location))
    app.add_handler(CallbackQueryHandler(handle_date_choice))
    print("Bot thời tiết đang chạy...")
    app.run_polling()
