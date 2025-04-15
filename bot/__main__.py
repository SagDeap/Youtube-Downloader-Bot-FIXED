from pyrogram import Client
import config
import asyncio
import atexit
import signal
import sys
import os

# Импортируем функции для работы с Telethon
from utils.telethon_helper import get_telethon_client, close_telethon_client
from telethon import TelegramClient
from telethon.sessions import StringSession

DOWNLOAD_LOCATION = "./Downloads"
BOT_TOKEN = config.BOT_TOKEN

APP_ID = config.APP_ID
API_HASH = config.API_HASH

# Глобальный клиент Telethon
telethon_client = None

plugins = dict(
    root="plugins",
)

# Функция для корректного завершения
async def shutdown():
    print("Закрытие сессий...")
    await close_telethon_client()
    print("Сессии закрыты, выход")

# Регистрируем функцию для вызова при выходе
def exit_handler():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(shutdown())

# Регистрируем обработчик завершения
atexit.register(exit_handler)

# Обработка сигналов завершения
def signal_handler(sig, frame):
    print(f"Получен сигнал {sig}, завершение работы...")
    sys.exit(0)

# Регистрируем обработчики сигналов
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

async def init_telethon():
    """Инициализация Telethon клиента"""
    global telethon_client
    
    try:
        # Инициализируем Telethon с StringSession вместо файловой сессии
        telethon_client = TelegramClient(
            StringSession(), 
            APP_ID,
            API_HASH
        )
        
        print("Подключение к Telegram через Telethon...")
        await telethon_client.start(bot_token=BOT_TOKEN)
        me = await telethon_client.get_me()
        print(f"Подключено к Telethon как {me.username} (ID: {me.id})")
        
        return telethon_client
    except Exception as e:
        print(f"Ошибка при инициализации Telethon: {e}")
        return None

async def main():
    # Инициализируем Telethon
    telethon_client = await init_telethon()
    if not telethon_client:
        print("Не удалось инициализировать Telethon, выход")
        return
    
    # Запускаем клиент Pyrogram
    app = Client(
        "YouTubeDlBot",
        bot_token=BOT_TOKEN,
        api_id=APP_ID,
        api_hash=API_HASH,
        plugins=plugins,
        workers=100
    )
    
    await app.start()
    print("Бот запущен!")
    
    # Ожидаем завершения (Ctrl+C)
    await asyncio.Event().wait()

if __name__ == "__main__":
    # Настраиваем asyncio для корректной работы с сигналами
    try:
        # В Python 3.10+ можно использовать более современный метод
        if sys.version_info >= (3, 10):
            asyncio.run(main())
        else:
            # Для совместимости с более старыми версиями Python
            loop = asyncio.get_event_loop()
            loop.run_until_complete(main())
    except KeyboardInterrupt:
        print("Завершение работы...")
    finally:
        # Обеспечиваем корректное закрытие соединений
        if telethon_client and telethon_client.is_connected():
            loop = asyncio.get_event_loop()
            loop.run_until_complete(telethon_client.disconnect())
        
        print("Сессии закрыты, выход")
