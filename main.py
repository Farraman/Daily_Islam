import os
import asyncio
import logging
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from aiohttp import web
from aiogram import Bot, Dispatcher, F
from aiogram.types import Update, Message, CallbackQuery
from aiogram.filters import CommandStart, Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
import requests

# ✅ Конфигурация
TOKEN = '7601592392:AAHcw0VODhZoTm899c4IAG-x1ZVtBE4--Cg'
CHANNEL_ID = -1002548380025
ADMIN_ID = 1812311983
WEBHOOK_HOST = 'https://daily-islam.onrender.com'
WEBHOOK_PATH = '/webhook'
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"
DEFAULT_POST_TIME = "09:00"
TIME_FILE = "post_time.txt"

# ✅ Настройка логирования
logging.basicConfig(level=logging.INFO)

bot = Bot(token=TOKEN)
dp = Dispatcher()

# ✅ Состояние ожидания ввода нового времени
waiting_for_time_input = set()

# ✅ Темы
daily_topics = [
    "Поделись Цитатой из Корана для надежды! ...",
    "Поделись аятом из Корана, который раскрывает любовь Аллаха ...",
    # ... остальные темы
]

def get_daily_prompt():
    index = datetime.now(ZoneInfo("Asia/Almaty")).timetuple().tm_yday % len(daily_topics)
    return daily_topics[index]

def load_post_time():
    if os.path.exists(TIME_FILE):
        with open(TIME_FILE, "r") as f:
            return f.read().strip()
    return DEFAULT_POST_TIME

def save_post_time(new_time):
    with open(TIME_FILE, "w") as f:
        f.write(new_time)

def was_posted_today():
    path = "last_post_date.txt"
    today_str = datetime.now(ZoneInfo("Asia/Almaty")).strftime("%Y-%m-%d")
    if os.path.exists(path):
        with open(path, "r") as f:
            return f.read().strip() == today_str
    return False

def update_last_post_date():
    with open("last_post_date.txt", "w") as f:
        f.write(datetime.now(ZoneInfo("Asia/Almaty")).strftime("%Y-%m-%d"))

# ✅ Отправка поста
async def send_daily_post():
    if was_posted_today():
        logging.info("✅ Пост уже был сегодня.")
        return

    prompt = get_daily_prompt()
    url = "https://api.intelligence.io.solutions/api/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer io-v2-..."
    }
    data = {
        "model": "deepseek-ai/DeepSeek-R1",
        "messages": [
            {"role": "system", "content": "Сделай исламский телеграм-пост на тему дня"},
            {"role": "user", "content": prompt}
        ]
    }

    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        result = response.json()
        text = result['choices'][0]['message']['content']
        bot_text = text.split('</think>\n\n')[1] if '</think>\n\n' in text else text
        await bot.send_message(chat_id=CHANNEL_ID, text=bot_text)
        update_last_post_date()
        logging.info("✅ Пост успешно отправлен.")
    except Exception as e:
        logging.error(f"❌ Ошибка отправки поста: {e}")

# ✅ Планировщик
async def daily_post():
    while True:
        now = datetime.now(ZoneInfo("Asia/Almaty"))
        hour, minute = map(int, load_post_time().split(":"))
        target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if now > target:
            target += timedelta(days=1)
        wait = (target - now).total_seconds()
        logging.info(f"⏳ Следующий пост в {target} (через {wait / 3600:.1f} ч)")
        await asyncio.sleep(wait)
        await send_daily_post()

# ✅ Команды
@dp.message(CommandStart())
async def start_cmd(message: Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("Привет! Я бот с ежедневными исламскими напоминаниями.")
        return

    kb = InlineKeyboardBuilder()
    kb.button(text="📤 Отправить пост сейчас", callback_data="post_now")
    kb.button(text="⏰ Изменить время", callback_data="change_time")
    kb.adjust(1)

    await message.answer("🕌 Добро пожаловать, админ!", reply_markup=kb.as_markup())

@dp.callback_query(F.data == "post_now")
async def cb_post_now(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return await callback.answer("❌ Только для администратора.", show_alert=True)
    await send_daily_post()
    await callback.answer("✅ Пост отправлен!")

@dp.callback_query(F.data == "change_time")
async def cb_change_time(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return await callback.answer("❌ Только для администратора.", show_alert=True)
    waiting_for_time_input.add(callback.from_user.id)
    await callback.message.answer("⏰ Введите новое время в формате HH:MM (например, 08:30)")
    await callback.answer()

@dp.message()
async def handle_text(message: Message):
    if message.from_user.id in waiting_for_time_input:
        try:
            datetime.strptime(message.text, "%H:%M")
            save_post_time(message.text)
            waiting_for_time_input.remove(message.from_user.id)
            await message.answer(f"✅ Время постинга изменено на {message.text}")
        except ValueError:
            await message.answer("❌ Неверный формат. Введите как HH:MM (например, 09:45).")

# ✅ Веб-сервер
async def on_startup(app):
    await bot.set_webhook(WEBHOOK_URL)
    asyncio.create_task(daily_post())
    logging.info("🌐 Вебхук установлен.")

async def on_shutdown(app):
    await bot.session.close()
    logging.info("❌ Сервер остановлен.")

async def handle_webhook(request):
    try:
        data = await request.json()
        update = Update.model_validate(data)
        await dp.feed_update(bot, update)
        return web.Response()
    except Exception as e:
        logging.error(f"Webhook error: {e}")
        return web.Response(status=500)

async def handle_index(request):
    return web.Response(text="Бот работает ✅")

# ✅ Запуск
app = web.Application()
app.on_startup.append(on_startup)
app.on_shutdown.append(on_shutdown)
app.router.add_post(WEBHOOK_PATH, handle_webhook)
app.router.add_get("/", handle_index)

if __name__ == "__main__":
    web.run_app(app, host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
