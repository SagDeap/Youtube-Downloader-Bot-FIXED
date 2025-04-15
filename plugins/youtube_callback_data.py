import asyncio
import os
import glob
import shutil
from datetime import datetime
from io import BytesIO

from pyrogram import Client, ContinuePropagation
from pyrogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InputMediaDocument,
    InputMediaVideo,
    InputMediaAudio
)

from helper.ffmfunc import duration
from helper.ytdlfunc import downloadvideocli, downloadaudiocli
from PIL import Image
from hachoir.metadata import extractMetadata
from hachoir.parser import createParser
from utils.telethon_helper import send_file_with_telethon

# Вспомогательная функция для очистки kwargs от нулевых значений
def clean_kwargs(kwargs):
    return {k: v for k, v in kwargs.items() if v not in (None, 0, '0')}

@Client.on_callback_query()
async def catch_youtube_fmtid(c, m):
    cb_data = m.data
    if cb_data.startswith("ytdata||"):
        yturl = cb_data.split("||")[-1]
        format_id = cb_data.split("||")[-2]
        media_type = cb_data.split("||")[-3].strip()
        print(media_type)
        if media_type == 'audio':
            buttons = InlineKeyboardMarkup([[InlineKeyboardButton(
                "Audio", callback_data=f"{media_type}||{format_id}||{yturl}"), InlineKeyboardButton("Document",
                                                                                                    callback_data=f"docaudio||{format_id}||{yturl}")]])
        else:
            buttons = InlineKeyboardMarkup([[InlineKeyboardButton(
                "Video", callback_data=f"{media_type}||{format_id}||{yturl}"), InlineKeyboardButton("Document",
                                                                                                    callback_data=f"docvideo||{format_id}||{yturl}")]])

        await m.edit_message_reply_markup(buttons)

    else:
        raise ContinuePropagation


@Client.on_callback_query()
async def catch_youtube_dldata(c, q):
    cb_data = q.data.strip()
    #print(q.message.chat.id)
    # Callback Data Check
    yturl = cb_data.split("||")[-1]
    format_id = cb_data.split("||")[-2]
    thumb_image_path = "/app/downloads" + \
        "/" + str(q.message.chat.id) + ".jpg"
    print(thumb_image_path)
    width = 0
    height = 0
    if os.path.exists(thumb_image_path):
        metadata = extractMetadata(createParser(thumb_image_path))
        #print(metadata)
        if metadata.has("width"):
            width = metadata.get("width")
        if metadata.has("height"):
            height = metadata.get("height")
        img = Image.open(thumb_image_path)
        if cb_data.startswith(("audio", "docaudio", "docvideo")):
            img.resize((320, height))
        else:
            img.resize((90, height))
        img.save(thumb_image_path, "JPEG")
     #   print(thumb_image_path)
    if not cb_data.startswith(("video", "audio", "docaudio", "docvideo")):
        print("no data found")
        raise ContinuePropagation

    filext = "%(title)s.%(ext)s"
    userdir = os.path.join(os.getcwd(), "downloads", str(q.message.chat.id))

    if not os.path.isdir(userdir):
        os.makedirs(userdir)
    await q.edit_message_reply_markup(
        InlineKeyboardMarkup([[InlineKeyboardButton("Скачивание...", callback_data="down")]]))
    filepath = os.path.join(userdir, filext)
    # await q.edit_message_reply_markup([[InlineKeyboardButton("Processing..")]])

    audio_command = [
        "youtube-dl",
        "-c",
        "--prefer-ffmpeg",
        "--extract-audio",
        "--audio-format", "mp3",
        "--audio-quality", format_id,
        "-o", filepath,
        yturl,
    ]

    video_command = [
        "youtube-dl",
        "-c",
        "--embed-subs",
        "-f", f"{format_id}+bestaudio",
        "-o", filepath,
        "--hls-prefer-ffmpeg", yturl]

    loop = asyncio.get_event_loop()

    filename = None
    file_type = None
    
    if cb_data.startswith("audio"):
        filename = await downloadaudiocli(audio_command)
        file_type = "audio"
    elif cb_data.startswith("video"):
        filename = await downloadvideocli(video_command)
        file_type = "video"
    elif cb_data.startswith("docaudio"):
        filename = await downloadaudiocli(audio_command)
        file_type = "docaudio"
    elif cb_data.startswith("docvideo"):
        filename = await downloadvideocli(video_command)
        file_type = "docvideo"
    
    if filename:
        loop.create_task(send_file_direct(c, q, filename, file_type, thumb_image_path))
    else:
        await q.edit_message_text("Ошибка: не удалось определить имя итогового файла после скачивания.")


async def send_file_direct(c, q, filename, file_type, thumb_path=None):
    try:
        await q.edit_message_reply_markup(
            InlineKeyboardMarkup([[InlineKeyboardButton("Отправка файла...", callback_data="down")]]))
        
        # Проверяем существование файла
        if not os.path.exists(filename):
            directory = os.path.dirname(filename)
            basename = os.path.basename(filename)
            print(f"Ищем файл в каталоге {directory} с базовым именем {basename}")
            
            # Ищем файл с таким же расширением
            if os.path.exists(directory):
                extension = os.path.splitext(basename)[1].lower()
                matching_files = []
                
                for file in os.listdir(directory):
                    if file.lower().endswith(extension):
                        matching_files.append(os.path.join(directory, file))
                        
                if matching_files:
                    # Берем самый новый файл
                    filename = max(matching_files, key=os.path.getmtime)
                    print(f"Найден альтернативный файл: {filename}")
                else:
                    await q.edit_message_text(f"Ошибка: файл не найден в каталоге {directory}")
                    return
            else:
                await q.edit_message_text(f"Ошибка: каталог {directory} не существует")
                return
        
        # Получаем имя файла для отображения в подписи
        caption = os.path.basename(filename)
        chat_id = q.message.chat.id
        
        # Обновляем сообщение
        await q.edit_message_text("Отправка файла через Telethon...")
        
        # Определяем, отправлять ли как видео
        is_video = False
        if file_type == "video":
            is_video = True
        elif file_type not in ["audio", "docaudio", "docvideo"]:
            # Если тип не задан явно, определяем по расширению
            ext = os.path.splitext(filename)[1].lower()
            if ext in ['.mp4', '.mkv', '.webm', '.avi', '.mov']:
                is_video = True
        
        print(f"Отправка файла {filename} (размер: {os.path.getsize(filename) / (1024*1024):.2f} МБ)")
        
        # Отправляем файл через Telethon
        max_retries = 3
        for attempt in range(1, max_retries + 1):
            try:
                print(f"Попытка {attempt} отправить файл")
                message_id = await send_file_with_telethon(
                    chat_id,
                    filename, 
                    caption=caption,
                    as_video=is_video,
                    thumb=thumb_path
                )
                
                if message_id:
                    print(f"Файл успешно отправлен через Telethon (попытка {attempt})")
                    # Удаляем сообщение-индикатор после успешной отправки
                    try:
                        await q.delete_messages(chat_id, q.message.message_id)
                    except Exception as del_err:
                        print(f"Ошибка при удалении сообщения: {del_err}")
                    return
                else:
                    print(f"Попытка {attempt} не удалась, сообщение не получено")
                    if attempt < max_retries:
                        await asyncio.sleep(2)  # Пауза перед следующей попыткой
            except Exception as attempt_err:
                print(f"Ошибка в попытке {attempt}: {attempt_err}")
                if attempt < max_retries:
                    await asyncio.sleep(2)
        
        # Если все попытки не удались
        await q.edit_message_text("Не удалось отправить файл. Пожалуйста, попробуйте еще раз.")
            
    except Exception as e:
        error_msg = f"Общая ошибка: {str(e)}"
        print(error_msg)
        try:
            await q.edit_message_text(error_msg)
        except:
            pass
    finally:
        # Пытаемся удалить файл только если он не используется Telethon
        try:
            import time
            # Даем время на завершение отправки
            time.sleep(3)
            
            if os.path.exists(filename):
                try:
                    os.remove(filename)
                    print(f"Файл успешно удален: {filename}")
                except Exception as e:
                    print(f"Не удалось удалить файл: {e}")
                    # Запланировать удаление файла позже
                    try:
                        import subprocess
                        command = f'ping localhost -n 10 > nul && del /f "{filename}"'
                        subprocess.Popen(command, shell=True)
                        print(f"Запланировано удаление файла через 10 секунд: {filename}")
                    except Exception as plan_e:
                        print(f"Не удалось запланировать удаление: {plan_e}")
            
            # Удаляем миниатюру, если она существует
            if thumb_path and os.path.exists(thumb_path):
                try:
                    os.remove(thumb_path)
                except Exception as e:
                    print(f"Ошибка при удалении миниатюры: {e}")
        except Exception as cleanup_err:
            print(f"Ошибка при очистке: {cleanup_err}")
