import asyncio
import logging
from aiohttp import web
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, Update
from aiogram.filters import Command
from aiogram.methods import DeleteWebhook
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import os
import requests

# 🔐 Твои данные
TOKEN = '7601592392:AAHcw0VODhZoTm899c4IAG-x1ZVtBE4--Cg'
CHANNEL_ID = '@Daily_Reminder_Islam'
ADMIN_ID = 1812311983
WEBHOOK_HOST = 'https://daily-islam.onrender.com'
WEBHOOK_PATH = '/webhook'
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"

# 🕘 Конфигурация времени
TIME_FILE = "post_time.txt"
DEFAULT_POST_TIME = "09:00"

# 📋 Настройка логирования
logging.basicConfig(level=logging.INFO)

# 🔧 Объекты бота
bot = Bot(token=TOKEN)
dp = Dispatcher()

# 🕌 Темы постов по дням
daily_topics = [
    "Поделись Цитатой из Корана для надежды! (не больше 50 слов,добавь немного смайликов для красоты и (всегда на всех постах пиши источник цитаты ввиде суры и аята) но не пиши кол-во слов",
    "Поделись аятом из Корана, который раскрывает любовь Аллаха к Своим рабам и объясни его смысл...",
    "Расскажи хадис Пророка ﷺ о любви Аллаха к верующим.(не больше 50 слов)",
    "Сделай мотивационный пост о том, как Аллах проявляет Свою любовь в трудностях...",
    "Поделись вдохновляющей историей из исламской традиции...",
    "Объясни, почему любовь Аллаха выше любви любого творения...",
    "Расскажи, какие качества человека делают его любимым для Аллаха...",
    "Сделай пост с напоминанием о том, что Аллах любит прощающих и кающихся..."
]

def load_post_time():
    if os.path.exists(TIME_FILE):
        with open(TIME_FILE, "r") as f:
            return f.read().strip()
    return DEFAULT_POST_TIME

def save_post_time(new_time):
    with open(TIME_FILE, "w") as f:
        f.write(new_time)

def get_daily_prompt():
    index = datetime.now(ZoneInfo("Asia/Almaty")).timetuple().tm_yday % len(daily_topics)
    return daily_topics[index]

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

async def send_daily_post():
    if was_posted_today():
        logging.info("✅ Пост уже был опубликован сегодня.")
        return

    try:
        prompt = get_daily_prompt()
        url = "https://api.intelligence.io.solutions/api/v1/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer io-v2-eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJvd25lciI6IjQzYzg3NGVlLWY1NGItNGU2Zi04NTM5LWEwZjllZmVkMmVhOSIsImV4cCI6NDkwMDQ5NDgwNX0.Ydko0GRPqtQJGSd2x6qH7BnmK9EKAQGoY9W_AxZUXzDjvtdw0JyfMbJw_OvU-IA3EAVkHH0lbDrQ4iocF3lQEg"  # ← Замени на свой валидный ключ!
        }
        data = {
            "model": "deepseek-ai/DeepSeek-R1",
            "messages": [
                {"role": "system", "content": "Сделай исламский телеграм-пост на тему дня"},
                {"role": "user", "content": prompt}
            ]
        }

        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        result = response.json()
        text = result['choices'][0]['message']['content']
        bot_text = text.split('</think>\n\n')[1] if '</think>\n\n' in text else text

        await bot.send_message(chat_id=CHANNEL_ID, text=bot_text, parse_mode="Markdown")
        update_last_post_date()
        logging.info("✅ Пост успешно отправлен.")

    except Exception as e:
        logging.error(f"❌ Ошибка при отправке поста: {e}")

# 🕐 Планировщик публикации
async def daily_post():
    while True:
        now = datetime.now(ZoneInfo("Asia/Almaty"))
        post_time = load_post_time()
        hour, minute = map(int, post_time.split(":"))
        target_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if now > target_time:
            target_time += timedelta(days=1)

        wait_seconds = (target_time - now).total_seconds()
        logging.info(f"⏳ Следующий пост в {post_time} (через {wait_seconds / 3600:.1f} часов)")
        await asyncio.sleep(wait_seconds)
        await send_daily_post()

# 🔘 Команды
@dp.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer("Привет! Я бот с ежедневными исламскими напоминаниями.")

@dp.message(Command("set_time"))
async def cmd_set_time(message: Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("❌ Эта команда только для администратора!")
        return

    args = message.text.split()
    if len(args) != 2 or ":" not in args[1]:
        await message.answer("⚠️ Используйте: /set_time HH:MM (например, /set_time 09:00)")
        return

    try:
        datetime.strptime(args[1], "%H:%M")
        save_post_time(args[1])
        await message.answer(f"✅ Время публикации изменено на {args[1]}!")
    except ValueError:
        await message.answer("❌ Неверный формат времени. Используйте HH:MM")

@dp.message(Command("post_now"))
async def cmd_post_now(message: Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("❌ Эта команда только для администратора!")
        return

    await send_daily_post()
    await message.answer("✅ Пост отправлен вручную!")

@dp.message()
async def handle_message(message: Message):
    await message.answer("Я работаю только по командам. Используйте /start, /set_time или /post_now.")

# 🌐 Webhook-обработчик
async def on_webhook(request):
    json_str = await request.json()
    update = Update(**json_str)
    await dp.feed_update(bot, update)  # ✅ Правильно для aiogram 3
    return web.Response(status=200)

# 🚀 Запуск
async def main():
    await bot.set_webhook(WEBHOOK_URL)
    app = web.Application()
    app.router.add_post(WEBHOOK_PATH, on_webhook)
    asyncio.create_task(daily_post())
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 8080)
    await site.start()
    logging.info("✅ Webhook и сервер запущены.")
    while True:
        await asyncio.sleep(3600)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.error("❌ Бот остановлен!")
