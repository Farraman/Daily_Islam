import os
import asyncio
import logging
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.types import Update
from aiogram.filters import CommandStart, Command
from aiogram.methods import DeleteWebhook
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

# ✅ Инициализация бота и диспетчера
bot = Bot(token=TOKEN)
dp = Dispatcher()

# ✅ Темы для ежедневных напоминаний
daily_topics = [
    "Поделись Цитатой из Корана для надежды! (не больше 50 слов,добавь немного смайликов для красоты и (всегда на всех постах пиши источник цитаты ввиде суры и аята) но не пиши кол-во слов",
    "Поделись аятом из Корана, который раскрывает любовь Аллаха к Своим рабам и объясни его смысл.(не больше 50 слов, добавь немного смайликов для красоты)(всегда на всех постах пиши источник цитаты ввиде суры и аята) но не пиши кол-во слов",
    "Расскажи хадис Пророка ﷺ о любви Аллаха к верующим.(не больше 50 слов)",
    "Сделай мотивационный пост о том, как Аллах проявляет Свою любовь в трудностях.(не больше 50 слов, добавь немного смайликов для красоты)(всегда на всех постах пиши источник цитаты ввиде суры и аята) но не пиши кол-во слов",
    "Поделись вдохновляющей историей из исламской традиции о том, как Аллах проявил милость к Своему рабу.(не больше 50 слов, добавь немного смайликов для красоты)(всегда на всех постах пиши источник цитаты ввиде суры и аята) но не пиши кол-во слов",
    "Объясни, почему любовь Аллаха выше любви любого творения.(не больше 50 слов, добавь немного смайликов для красоты)(всегда на всех постах пиши источник цитаты ввиде суры и аята) но не пиши кол-во слов",
    "Расскажи, какие качества человека делают его любимым для Аллаха.(не больше 50 слов, добавь немного смайликов для красоты)(всегда на всех постах пиши источник цитаты ввиде суры и аята) но не пиши кол-во слов",
    "Сделай пост с напоминанием о том, что Аллах любит прощающих и кающихся.(не больше 50 слов, добавь немного смайликов для красоты)(всегда на всех постах пиши источник цитаты ввиде суры и аята) но не пиши кол-во слов"
]

# ✅ Вспомогательные функции
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
        "Authorization": "Bearer io-v2-eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJvd25lciI6IjQzYzg3NGVlLWY1NGItNGU2Zi04NTM5LWEwZjllZmVkMmVhOSIsImV4cCI6NDkwMDQ5NDgwNX0.Ydko0GRPqtQJGSd2x6qH7BnmK9EKAQGoY9W_AxZUXzDjvtdw0JyfMbJw_OvU-IA3EAVkHH0lbDrQ4iocF3lQEg"  # ❗️Замени на свой реальный API токен
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

        await bot.send_message(chat_id=CHANNEL_ID, text=bot_text, parse_mode="Markdown")
        update_last_post_date()
        logging.info("✅ Пост успешно отправлен.")
    except Exception as e:
        logging.error(f"❌ Ошибка отправки поста: {e}")

# ✅ Планировщик
async def daily_post():
    while True:
        now = datetime.now(ZoneInfo("Asia/Almaty"))
        post_time = load_post_time()
        hour, minute = map(int, post_time.split(":"))
        target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if now > target:
            target += timedelta(days=1)
        wait = (target - now).total_seconds()
        logging.info(f"⏳ Следующий пост в {post_time} (через {wait / 3600:.1f} ч)")
        await asyncio.sleep(wait)
        await send_daily_post()

# ✅ Обработчики команд
@dp.message(CommandStart())
async def start_cmd(message):
    await message.answer("Привет! Я бот с ежедневными исламскими напоминаниями.")

@dp.message(Command("set_time"))
async def set_time_cmd(message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("❌ Только для администратора.")
        return

    parts = message.text.strip().split()
    if len(parts) != 2 or ":" not in parts[1]:
        await message.answer("⚠️ Используй формат /set_time HH:MM")
        return

    try:
        datetime.strptime(parts[1], "%H:%M")
        save_post_time(parts[1])
        await message.answer(f"✅ Время изменено на {parts[1]}")
    except ValueError:
        await message.answer("❌ Неверный формат времени.")

@dp.message(Command("post_now"))
async def post_now_cmd(message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("❌ Только для администратора.")
        return
    await send_daily_post()
    await message.answer("✅ Пост отправлен вручную!")

# ✅ Веб-сервер aiohttp
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
