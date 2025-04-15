import os
import asyncio
from telethon import TelegramClient
from telethon.sessions import StringSession
import config
from datetime import datetime

# Клиент Telethon
_telethon_client = None

async def get_telethon_client():
    """Получить или инициализировать клиент Telethon"""
    global _telethon_client
    
    if _telethon_client is None:
        # Проверяем, инициализирован ли клиент в main.py
        try:
            from bot.__main__ import telethon_client
            if telethon_client and telethon_client.is_connected():
                _telethon_client = telethon_client
                return _telethon_client
        except ImportError:
            pass
        
        # Создаем клиент Telethon с использованием StringSession (не использует SQLite)
        _telethon_client = TelegramClient(
            StringSession(), 
            config.APP_ID, 
            config.API_HASH
        )
        await _telethon_client.start(bot_token=config.BOT_TOKEN)
        
    return _telethon_client

# Упрощенная функция отправки файла
async def send_file_simple(chat_id, file_path, caption=None, as_video=False, thumb=None):
    """Упрощенная функция отправки файла через Telethon"""
    try:
        client = TelegramClient(
            StringSession(), 
            config.APP_ID, 
            config.API_HASH
        )
        await client.start(bot_token=config.BOT_TOKEN)
        
        if not os.path.exists(file_path):
            print(f"Файл не найден: {file_path}")
            return None
            
        print(f"Отправка файла: {file_path}")
        message = await client.send_file(
            chat_id,
            file_path,
            caption=caption,
            supports_streaming=as_video
        )
        
        print("Файл успешно отправлен")
        await client.disconnect()
        return message.id
    except Exception as e:
        print(f"Ошибка при отправке файла: {e}")
        if 'client' in locals() and client.is_connected():
            await client.disconnect()
        return None

async def send_file_with_telethon(chat_id, file_path, caption=None, as_video=False, thumb=None):
    """Отправить файл с использованием Telethon"""
    
    # Сначала пробуем простую отправку через временный клиент
    try:
        result = await send_file_simple(chat_id, file_path, caption, as_video, thumb)
        if result:
            return result
    except Exception as simple_error:
        print(f"Простая отправка не удалась: {simple_error}")
    
    # Если простой способ не сработал, используем более сложный
    try:
        # Проверяем существование файла
        if not os.path.exists(file_path):
            print(f"Telethon: Файл не найден: {file_path}")
            
            # Ищем похожий файл в каталоге
            directory = os.path.dirname(file_path)
            if os.path.exists(directory):
                ext = os.path.splitext(file_path)[1].lower()
                matching_files = [os.path.join(directory, f) for f in os.listdir(directory) 
                                 if f.lower().endswith(ext)]
                
                if matching_files:
                    # Используем самый новый файл
                    file_path = max(matching_files, key=os.path.getmtime)
                    print(f"Telethon: Найден альтернативный файл: {file_path}")
                else:
                    return None
            else:
                return None
        
        # Попытка 3: Копирование во временный файл с простым именем
        try:
            import tempfile
            import shutil
            
            # Создаем временный файл с простым именем
            temp_dir = tempfile.gettempdir()
            filename = os.path.basename(file_path)
            temp_file = os.path.join(temp_dir, f"temp_file_{int(datetime.now().timestamp())}{os.path.splitext(filename)[1]}")
            
            # Копируем файл
            shutil.copy2(file_path, temp_file)
            print(f"Создан временный файл: {temp_file}")
            
            try:
                # Создаем новый клиент для каждой отправки
                client = TelegramClient(
                    StringSession(), 
                    config.APP_ID, 
                    config.API_HASH
                )
                await client.start(bot_token=config.BOT_TOKEN)
                
                message = await client.send_file(
                    chat_id,
                    temp_file,
                    caption=caption,
                    supports_streaming=as_video
                )
                
                print("Telethon: Файл успешно отправлен через временный файл")
                await client.disconnect()
                return message.id
                
            except Exception as send_error:
                print(f"Ошибка при отправке: {send_error}")
                return None
                
            finally:
                # Удаляем временный файл
                try:
                    if os.path.exists(temp_file):
                        os.remove(temp_file)
                        print(f"Временный файл удален: {temp_file}")
                except Exception as del_error:
                    print(f"Ошибка при удалении временного файла: {del_error}")
                
                # Отключаем клиент
                if 'client' in locals() and client.is_connected():
                    await client.disconnect()
        
        except Exception as copy_error:
            print(f"Ошибка при создании временного файла: {copy_error}")
            return None
            
    except Exception as e:
        print(f"Telethon: Общая ошибка при отправке файла: {e}")
        return None
        
# Закрыть клиент Telethon при завершении работы
async def close_telethon_client():
    global _telethon_client
    if _telethon_client and _telethon_client.is_connected():
        await _telethon_client.disconnect()
        _telethon_client = None 