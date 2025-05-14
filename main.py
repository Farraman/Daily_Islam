import asyncio
import logging
from aiohttp import web
import requests
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from aiogram import Bot, Dispatcher
from aiogram.types import Update, Message
from aiogram.filters import Command
from aiogram.methods import DeleteWebhook
import os

# === ДАННЫЕ БОТА ===
TOKEN = '7601592392:AAHcw0VODhZoTm899c4IAG-x1ZVtBE4--Cg'
CHANNEL_ID = '@Daily_Reminder_Islam'
ADMIN_ID = 1812311983
WEBHOOK_HOST = 'https://daily-islam.onrender.com'
WEBHOOK_PATH = '/webhook'
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"
TIME_FILE = "post_time.txt"
DEFAULT_POST_TIME = "09:00"
PORT = int(os.environ.get('PORT', 8080))

# === ЛОГИ ===
logging.basicConfig(level=logging.INFO)

# === ИНИЦИАЛИЗАЦИЯ ===
bot = Bot(token=TOKEN)
dp = Dispatcher()

# === ТЕМЫ ===
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

# === ХЕЛПЕРЫ ===
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

# === ОТПРАВКА ПОСТА ===
async def send_daily_post():
    if was_posted_today():
        logging.info("✅ Пост уже был опубликован сегодня.")
        return

    try:
        prompt = get_daily_prompt()
        url = "https://api.intelligence.io.solutions/api/v1/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer io-v2-eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJvd25lciI6IjQzYzg3NGVlLWY1NGItNGU2Zi04NTM5LWEwZjllZmVkMmVhOSIsImV4cCI6NDkwMDQ5NDgwNX0.Ydko0GRPqtQJGSd2x6qH7BnmK9EKAQGoY9W_AxZUXzDjvtdw0JyfMbJw_OvU-IA3EAVkHH0lbDrQ4iocF3lQEg"  # <-- Твой токен API
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
        text = response.json()['choices'][0]['message']['content']
        bot_text = text.split('</think>\n\n')[1] if '</think>\n\n' in text else text

        await bot.send_message(chat_id=CHANNEL_ID, text=bot_text, parse_mode="Markdown")
        update_last_post_date()
        logging.info("✅ Пост успешно отправлен.")
    except Exception as e:
        logging.error(f"❌ Ошибка при отправке поста: {e}")

# === ЗАДАЧА ===
async def daily_post():
    while True:
        now = datetime.now(ZoneInfo("Asia/Almaty"))
        target_hour, target_minute = map(int, load_post_time().split(":"))
        target_time = now.replace(hour=target_hour, minute=target_minute, second=0, microsecond=0)
        if now > target_time:
            target_time += timedelta(days=1)
        wait_seconds = (target_time - now).total_seconds()
        logging.info(f"⏳ Следующий пост в {target_time.strftime('%H:%M')} (через {wait_seconds/3600:.1f} часов)")
        await asyncio.sleep(wait_seconds)
        await send_daily_post()

# === ХЕНДЛЕРЫ ===
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
        await message.answer("⚠️ Используйте: /set_time HH:MM")
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

# === ОБРАБОТКА ОБЫЧНЫХ СООБЩЕНИЙ ===
@dp.message()
async def handle_message(message: Message):
    await message.answer("Я принимаю только команды. Попробуйте /start.")

# === ВЕБХУК ===
async def on_startup():
    await bot.set_webhook(WEBHOOK_URL, drop_pending_updates=True)
    asyncio.create_task(daily_post())

async def on_webhook(request):
    try:
        data = await request.json()
        update = Update.model_validate(data)
        await dp.feed_update(bot, update)
        return web.Response()
    except Exception as e:
        logging.error(f"Ошибка при обработке вебхука: {e}")
        return web.Response(status=500)

# === ХЕЛСЧЕК ===
@web.get("/")
async def root(request):
    return web.Response(text="Bot is alive ✅")

# === ПРИЛОЖЕНИЕ ===
app = web.Application()
app.router.add_get("/", root)
app.router.add_post(WEBHOOK_PATH, on_webhook)

if __name__ == "__main__":
    asyncio.run(on_startup())
    web.run_app(app, host="0.0.0.0", port=PORT)
