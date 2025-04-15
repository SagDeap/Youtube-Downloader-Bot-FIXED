from __future__ import unicode_literals
from pyrogram import Client, filters, StopPropagation
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
import youtube_dl
from utils.util import humanbytes
import asyncio
import re
import os


def buttonmap(item):
    quality = item['format']
    if "audio" in quality:
        return [InlineKeyboardButton(f"{quality} 🎵 {humanbytes(item['filesize'])}",
                                     callback_data=f"ytdata||audio||{item['format_id']}||{item['yturl']}")]
    else:
        return [InlineKeyboardButton(f"{quality} 📹 {humanbytes(item['filesize'])}",
                                     callback_data=f"ytdata||video||{item['format_id']}||{item['yturl']}")]

# Return a array of Buttons
def create_buttons(quailitylist):
    return map(buttonmap, quailitylist)


# extract Youtube info
def extractYt(yturl):
    ydl = youtube_dl.YoutubeDL()
    with ydl:
        qualityList = []
        try:
            r = ydl.extract_info(yturl, download=False)
        except Exception as e:
            print("Ошибка youtube-dl:", e)
            raise
        for format in r['formats']:
            # Filter dash video(without audio)
            if not "dash" in str(format['format']).lower():
                filesize = format.get('filesize') or 0
                qualityList.append(
                {"format": format['format'], "filesize": filesize, "format_id": format['format_id'],
                 "yturl": yturl})

        return r['title'], r['thumbnail'], qualityList


#  Need to work on progress

# def downloadyt(url, fmid, custom_progress):
#     ydl_opts = {
#         'format': f"{fmid}+bestaudio",
#         "outtmpl": "test+.%(ext)s",
#         'noplaylist': True,
#         'progress_hooks': [custom_progress],
#     }
#     with youtube_dl.YoutubeDL(ydl_opts) as ydl:
#         ydl.download([url])


# https://github.com/SpEcHiDe/AnyDLBot

async def downloadvideocli(command_to_exec):
    process = await asyncio.create_subprocess_exec(
        *command_to_exec,
        # stdout must a pipe to be accessible as process.stdout
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE, )
    stdout, stderr = await process.communicate()
    e_response = stderr.decode().strip()
    t_response = stdout.decode().strip()
    print("STDOUT:", t_response)
    print("STDERR:", e_response)
    
    # Функция для проверки существования файла (с учетом проблем кодировки)
    def check_file_exists(file_path):
        # Прямая проверка
        if os.path.exists(file_path):
            return file_path
            
        # Проверка в каталоге
        dir_path = os.path.dirname(file_path)
        if not os.path.exists(dir_path):
            return None
            
        # Проверка файлов в каталоге
        base_name = os.path.basename(file_path)
        extension = os.path.splitext(base_name)[1].lower()
        
        matching_files = []
        for file in os.listdir(dir_path):
            if file.lower().endswith(extension):
                # Возможно совпадение имени с проблемами кодировки
                matching_files.append(os.path.join(dir_path, file))
        
        if matching_files:
            # Возвращаем самый новый файл
            return max(matching_files, key=os.path.getmtime)
        return None
    
    # Поиск строки с "Merging formats into"
    if "Merging formats into" in t_response:
        try:
            # Получаем имя файла из строки
            merge_line = None
            for line in t_response.split("\n"):
                if "Merging formats into" in line:
                    merge_line = line
                    break
                    
            if merge_line:
                # Извлекаем путь к файлу, учитывая двойные кавычки
                parts = merge_line.split("Merging formats into")
                quoted_filename = parts[1].strip()
                if quoted_filename.startswith('"') and quoted_filename.endswith('"'):
                    filename = quoted_filename[1:-1]  # Убираем кавычки
                else:
                    filename = quoted_filename
                    
                print(f"Найден путь к итоговому файлу: {filename}")
                
                # Проверяем, существует ли файл (с учетом проблем кодировки)
                checked_file = check_file_exists(filename)
                if checked_file:
                    return checked_file
                
                # Если файл не найден, возвращаем исходный путь
                return filename
                
        except Exception as e:
            print("Ошибка парсинга имени файла:", e)
    
    # Если не нашли через Merging, ищем через Destination
    elif "Destination" in t_response:
        try:
            # Найдём все пути к файлам, возьмём последний
            matches = []
            for line in t_response.split("\n"):
                if "Destination:" in line:
                    parts = line.split("Destination:")
                    file_path = parts[1].strip()
                    matches.append(file_path)
            
            if matches:
                # Берем последний файл с расширением .mkv
                for match in reversed(matches):
                    if match.lower().endswith(".mkv"):
                        print(f"Найден путь к итоговому файлу через Destination: {match}")
                        checked_file = check_file_exists(match)
                        if checked_file:
                            return checked_file
                
                # Если .mkv не найден, берем последний файл
                filename = matches[-1].strip()
                print(f"Найден путь к итоговому файлу через Destination: {filename}")
                checked_file = check_file_exists(filename)
                if checked_file:
                    return checked_file
                return filename
                
        except Exception as e:
            print("Ошибка парсинга имени файла (Destination):", e)
    
    # Если по Destination не нашли, ищем строку "has already been downloaded"
    elif "[download]" in t_response and "has already been downloaded and merged" in t_response:
        # Найти строку с любым файлом
        for line in t_response.split("\n"):
            if "[download]" in line and "has already been downloaded and merged" in line:
                try:
                    # Извлекаем путь к файлу из строки
                    parts = line.split("[download] ")
                    if len(parts) > 1:
                        file_path = parts[1].split(" has already been downloaded")[0].strip()
                        print(f"Найден уже скачанный файл: {file_path}")
                        checked_file = check_file_exists(file_path)
                        if checked_file:
                            return checked_file
                        return file_path
                except Exception as e:
                    print("Ошибка парсинга имени файла (already downloaded):", e)
    
    # Если ничего не нашли, проверяем каталог на наличие .mkv файлов
    try:
        directory = os.path.dirname(command_to_exec[-2])  # Путь к каталогу выходного файла
        if "%(title)s" in command_to_exec[-2]:
            # Если используется шаблон имени файла, получаем каталог
            parts = command_to_exec[-2].split(os.sep)
            directory = os.sep.join(parts[:-1])
        
        # Ищем .mkv файлы в каталоге
        if os.path.exists(directory):
            mkv_files = [os.path.join(directory, f) for f in os.listdir(directory) if f.lower().endswith(".mkv")]
            if mkv_files:
                # Берем самый новый файл
                newest_file = max(mkv_files, key=os.path.getmtime)
                print(f"Найден новейший .mkv файл в каталоге: {newest_file}")
                return newest_file
    except Exception as e:
        print("Ошибка при поиске .mkv файлов в каталоге:", e)
    
    print("Не удалось найти имя файла в выводе youtube-dl")
    return None


async def downloadaudiocli(command_to_exec):
    process = await asyncio.create_subprocess_exec(
        *command_to_exec,
        # stdout must a pipe to be accessible as process.stdout
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE, )
    stdout, stderr = await process.communicate()
    e_response = stderr.decode().strip()
    t_response = stdout.decode().strip()
    print("STDOUT (аудио):", t_response)
    print("STDERR (аудио):", e_response)
    
    # Функция для проверки существования файла (с учетом проблем кодировки)
    def check_file_exists(file_path):
        # Прямая проверка
        if os.path.exists(file_path):
            return file_path
            
        # Проверка в каталоге
        dir_path = os.path.dirname(file_path)
        if not os.path.exists(dir_path):
            return None
            
        # Проверка файлов в каталоге
        base_name = os.path.basename(file_path)
        extension = os.path.splitext(base_name)[1].lower()
        
        matching_files = []
        for file in os.listdir(dir_path):
            if file.lower().endswith(extension):
                # Возможно совпадение имени с проблемами кодировки
                matching_files.append(os.path.join(dir_path, file))
        
        if matching_files:
            # Возвращаем самый новый файл
            return max(matching_files, key=os.path.getmtime)
        return None

    try:
        # Поиск строки с "Destination"
        matches = []
        for line in t_response.split("\n"):
            if "Destination:" in line:
                parts = line.split("Destination:")
                file_path = parts[1].strip()
                matches.append(file_path)
        
        if matches:
            # Берем последний файл с расширением .mp3
            for match in reversed(matches):
                if match.lower().endswith(".mp3"):
                    print(f"Найден аудиофайл (mp3): {match}")
                    checked_file = check_file_exists(match)
                    if checked_file:
                        return checked_file
            
            # Если .mp3 не найден, берем последний файл
            filename = matches[-1].strip()
            print(f"Найден аудиофайл: {filename}")
            checked_file = check_file_exists(filename)
            if checked_file:
                return checked_file
            return filename
    except Exception as e:
        print(f"Ошибка при поиске пути аудиофайла по Destination: {e}")
    
    try:
        # Если не нашли через Destination, ищем "has already been downloaded"
        for line in t_response.split("\n"):
            if "[download]" in line and "has already been downloaded" in line:
                parts = line.split("[download] ")
                if len(parts) > 1:
                    file_path = parts[1].split(" has already been downloaded")[0].strip()
                    print(f"Найден уже скачанный аудиофайл: {file_path}")
                    checked_file = check_file_exists(file_path)
                    if checked_file:
                        return checked_file
                    return file_path
    except Exception as e:
        print(f"Ошибка при поиске уже скачанного аудиофайла: {e}")
    
    # Если другие методы не сработали, ищем MP3 файлы в выходном каталоге
    try:
        directory = os.path.dirname(command_to_exec[-2])  # Путь к каталогу выходного файла
        if "%(title)s" in command_to_exec[-2]:
            # Если используется шаблон имени файла, получаем каталог
            parts = command_to_exec[-2].split(os.sep)
            directory = os.sep.join(parts[:-1])
        
        # Ищем .mp3 файлы в каталоге
        if os.path.exists(directory):
            mp3_files = [os.path.join(directory, f) for f in os.listdir(directory) if f.lower().endswith(".mp3")]
            if mp3_files:
                # Берем самый новый файл
                newest_file = max(mp3_files, key=os.path.getmtime)
                print(f"Найден новейший .mp3 файл в каталоге: {newest_file}")
                return newest_file
    except Exception as e:
        print(f"Ошибка при поиске .mp3 файлов в каталоге: {e}")
    
    # Если все методы не сработали, используем старый способ
    try:
        filename = t_response.split("Destination")[-1].split("Deleting")[0].split(":")[-1].strip()
        print(f"Определен аудиофайл по старому алгоритму: {filename}")
        checked_file = check_file_exists(filename)
        if checked_file:
            return checked_file
        return filename
    except Exception as e:
        print(f"Ошибка при определении имени аудиофайла по старому алгоритму: {e}")
        return None
