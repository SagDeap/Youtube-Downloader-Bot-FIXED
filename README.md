# YouTube Downloader Bot 📥



## 🔥 Улучшения в этой версии

- ✅ **Исправлена проблема с отправкой файлов** - устранена ошибка "'str' object has no attribute 'name'"
- ✅ **Поддержка кириллицы и Unicode** - корректная работа с специальными символами в именах файлов
- ✅ **Надежная отправка файлов** - использование Telethon вместо Pyrogram для отправки файлов
- ✅ **Улучшенная обработка ошибок** - более надежная работа при возникновении исключений
- ✅ **Автоматическая очистка файлов** - удаление временных файлов после отправки

## 📋 Требования

```
- Python 3.7+
- ffmpeg
- youtube-dl или yt-dlp
```

## 🔧 Установка зависимостей

```bash
pip install -r requirements.txt
```

## ⚙️ Настройка бота

1. **Создайте бота у @BotFather в Telegram и получите токен**

2. **Получите API ID и API HASH на сайте [my.telegram.org](https://my.telegram.org/)**

3. **Настройте конфигурацию бота одним из способов:**

   **Способ 1: Использование config.py (рекомендуется)**
   ```bash
   # Скопируйте пример конфигурационного файла
   cp config.example.py config.py
   
   # Откройте файл в редакторе и замените заглушки своими данными
   nano config.py
   ```

   **Способ 2: Использование .env файла**
   ```bash
   # Скопируйте пример .env файла
   cp .env.example .env
   
   # Откройте файл в редакторе и замените заглушки своими данными
   nano .env
   ```

   В обоих случаях вам нужно заменить:
   - `BOT_TOKEN` - токен вашего бота от @BotFather
   - `APP_ID` - ваш API ID с my.telegram.org
   - `API_HASH` - ваш API Hash с my.telegram.org

## 🚀 Запуск бота

```bash
python -m bot
```

## 🎯 Использование

1. Отправьте боту ссылку на YouTube видео
2. Выберите формат видео или аудио
3. Выберите качество
4. Дождитесь загрузки и получите файл в чате

*Файлы не отправляются**: Добавлены различные методы отправки с автоматическим переключением между ними при ошибках

## 📝 Примечания

- Поддерживаются как видео, так и аудио форматы
- Для видео доступна отправка в виде видеофайла или документа
- Для аудио доступна отправка в виде аудиофайла или документа

## 👨‍💻 Разработка

Этот бот является улучшенной версией [aryanvikash/Youtube-Downloader-Bot](https://github.com/aryanvikash/Youtube-Downloader-Bot) с исправленными ошибками и расширенной функциональностью.

## 🙏 Благодарности

- [Spechide](https://github.com/SpEcHiDe) за AnyDlBot
- [HasibulKabir](https://github.com/HasibulKabir)
- [aryanvikash](https://github.com/aryanvikash) за оригинальный бот

[![Deploy](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy?template=https://github.com/aryanvikash/Youtube-Downloader-Bot/tree/master)