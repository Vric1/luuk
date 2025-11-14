import logging
import requests
import asyncio
import os
import io
import tempfile
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

# 👉 КОНФИГУРАЦИЯ БОТА
# Пробуем загрузить из переменных окружения, иначе - из констант
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "8491937834:AAF7rHBKjNepJ8VKNiZUaywhBc6eUWtRtUQ")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "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")
MODEL_NAME = os.getenv("MODEL_NAME", "tngtech/deepseek-r1t2-chimera:free")

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Хранилище данных пользователей (в продакшене используйте БД)
user_data = {}

# ФУНКЦИЯ ДЛЯ OPENROUTER API
def call_openrouter(prompt: str, system_prompt: str = None) -> str:
    """Вызов OpenRouter API для получения ответа от ИИ"""
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://t.me/your_rp_bot",
        "X-Title": "Telegram RP Bot",
    }
    
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})
    
    data = {
        "model": MODEL_NAME,
        "messages": messages,
        "max_tokens": 1000,
        "temperature": 0.8
    }

    try:
        resp = requests.post(url, headers=headers, json=data, timeout=60)
        resp.raise_for_status()
        j = resp.json()
        return j["choices"][0]["message"]["content"]
    except Exception as e:
        logger.error(f"OpenRouter API ошибка: {e}")
        return "😔 Ошибка ИИ, попробуй чуть позже..."

# ФУНКЦИЯ ДЛЯ СОЗДАНИЯ ФАЙЛОВ
def generate_file_content(prompt: str, file_type: str = "txt") -> tuple[str, str]:
    """Генерация содержимого для файла через ИИ"""
    system_prompt = f"""Ты - специалист по созданию файлов. На основе запроса пользователя создай контент для файла типа "{file_type}".

Правила:
1. Отвечай только содержимым файла
2. Не добавляй комментарии или объяснения
3. Создавай качественный и полезный контент
4. Начинай ответ сразу с содержимого"""
    
    content = call_openrouter(prompt, system_prompt)
    
    # Определяем имя файла
    import re
    safe_name = re.sub(r'[^a-zA-Z0-9а-яА-Я_-]', '_', prompt[:30])
    filename = f"{safe_name}.{file_type}"
    
    return content, filename

# ФУНКЦИЯ ДЛЯ ПРЕОБРАЗОВАНИЯ ТЕКСТА В ГОЛОС
def text_to_speech(text: str, language: str = "ru") -> io.BytesIO:
    """Преобразование текста в голос через бесплатный TTS API"""
    try:
        # Ограничиваем длину текста (Google TTS лимит ~200 символов)
        if len(text) > 200:
            text = text[:200] + "..."
        
        # Удаляем невалидные символы
        import urllib.parse
        clean_text = text.replace('\n', ' ').replace('\r', ' ').strip()
        
        # Бесплатный TTS через Google Translate API
        encoded_text = urllib.parse.quote(clean_text)
        
        # Поддерживаемые языки: ru, en, es, fr, de, it, pt, ja, ko, zh
        supported_langs = {"ru", "en", "es", "fr", "de", "it", "pt", "ja", "ko", "zh"}
        if language not in supported_langs:
            language = "ru"
        
        # URL для Google TTS
        tts_url = f"https://translate.google.com/translate_tts?ie=UTF-8&q={encoded_text}&tl={language}&client=tw-ob"
        
        # Заголовки для имитации браузера
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # Запрос к TTS API
        response = requests.get(tts_url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # Возвращаем аудио файл
        audio_buffer = io.BytesIO(response.content)
        audio_buffer.name = "voice.mp3"
        return audio_buffer
        
    except Exception as e:
        logger.error(f"TTS error: {e}")
        return None

# РП команды
RP_ACTIONS = {
    'hug': '🤗 обнял(а)',
    'kiss': '💋 поцеловал(а)',
    'pat': '👋 погладил(а)',
    'slap': '👋 ударил(а)',
    'poke': '👉 ткнул(а)',
    'bite': '😬 укусил(а)',
    'punch': '👊 ударил(а)',
    'kill': '💀 убил(а)',
    'feed': '🍕 накормил(а)',
    'cuddle': '🤗 обнял(а) крепко',
    'cry': '😢 плачет рядом с',
    'smile': '😊 улыбается',
    'dance': '💃 танцует с',
    'wave': '👋 машет рукой',
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start"""
    user = update.effective_user
    welcome_text = f"""
👋 Привет, {user.first_name}!

Я РП бот с ИИ для ролевых игр в Telegram!

📝 Доступные команды:
/profile - Твой профиль
/rp - Список РП команд
/ai - Чат с ИИ (ролевая игра)
/file - Создать файл через ИИ
/voice - Преобразовать текст в голос
/help - Помощь

🎭 РП команды:
/hug @username - обнять пользователя
/kiss - поцеловать (ответом на сообщение)

🤖 ИИ возможности:
• Просто напиши мне - я отвечу как ролевой персонаж!
• Создаю файлы: TXT, CSV, JSON, HTML, Python и другие!
• Преобразую текст в голосовые сообщения!
"""
    await update.message.reply_text(welcome_text)
    
    # Инициализация профиля пользователя
    if user.id not in user_data:
        user_data[user.id] = {
            'username': user.username or user.first_name,
            'rp_count': 0,
            'level': 1,
            'exp': 0
        }

async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать профиль пользователя"""
    user = update.effective_user
    
    if user.id not in user_data:
        user_data[user.id] = {
            'username': user.username or user.first_name,
            'rp_count': 0,
            'level': 1,
            'exp': 0
        }
    
    data = user_data[user.id]
    profile_text = f"""
👤 Профиль {user.first_name}

🎭 РП действий: {data['rp_count']}
⭐ Уровень: {data['level']}
✨ Опыт: {data['exp']}/100
"""
    await update.message.reply_text(profile_text)

async def rp_commands(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать список РП команд"""
    commands_text = "🎭 Доступные РП команды:\n\n"
    for cmd, action in RP_ACTIONS.items():
        commands_text += f"/{cmd} - {action}\n"
    
    commands_text += "\n💡 Используй команды с @username или ответом на сообщение"
    await update.message.reply_text(commands_text)

async def handle_rp_action(update: Update, context: ContextTypes.DEFAULT_TYPE, action_name: str):
    """Обработка РП действия"""
    user = update.effective_user
    
    # Инициализация данных пользователя
    if user.id not in user_data:
        user_data[user.id] = {
            'username': user.username or user.first_name,
            'rp_count': 0,
            'level': 1,
            'exp': 0
        }
    
    # Определяем цель действия
    target = None
    target_name = None
    
    # Проверка ответа на сообщение
    if update.message.reply_to_message:
        target = update.message.reply_to_message.from_user
        target_name = target.first_name
    # Проверка упоминания в тексте
    elif context.args:
        target_name = ' '.join(context.args)
    
    if not target_name:
        await update.message.reply_text(
            "❌ Укажи пользователя через @username или ответь на его сообщение!"
        )
        return
    
    # Формируем текст действия
    action_text = RP_ACTIONS.get(action_name, 'сделал что-то с')
    rp_text = f"🎭 {user.first_name} {action_text} {target_name}!"
    
    # Обновляем статистику
    user_data[user.id]['rp_count'] += 1
    user_data[user.id]['exp'] += 5
    
    # Повышение уровня
    if user_data[user.id]['exp'] >= 100:
        user_data[user.id]['level'] += 1
        user_data[user.id]['exp'] = 0
        rp_text += f"\n\n⭐ {user.first_name} повысил уровень до {user_data[user.id]['level']}!"
    
    await update.message.reply_text(rp_text)

# Создаем обработчики для каждой РП команды
async def hug(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await handle_rp_action(update, context, 'hug')

async def kiss(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await handle_rp_action(update, context, 'kiss')

async def pat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await handle_rp_action(update, context, 'pat')

async def slap(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await handle_rp_action(update, context, 'slap')

async def poke(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await handle_rp_action(update, context, 'poke')

async def bite(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await handle_rp_action(update, context, 'bite')

async def punch(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await handle_rp_action(update, context, 'punch')

async def kill(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await handle_rp_action(update, context, 'kill')

async def feed(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await handle_rp_action(update, context, 'feed')

async def cuddle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await handle_rp_action(update, context, 'cuddle')

async def cry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await handle_rp_action(update, context, 'cry')

async def smile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await handle_rp_action(update, context, 'smile')

async def dance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await handle_rp_action(update, context, 'dance')

async def wave(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await handle_rp_action(update, context, 'wave')

async def ai_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда для ИИ чата"""
    user = update.effective_user
    
    if not context.args:
        await update.message.reply_text(
            "🤖 Напиши мне что-нибудь после /ai \n\n"
            "Пример: /ai Привет! Как дела?"
        )
        return
    
    user_message = " ".join(context.args)
    await update.message.chat.send_action("typing")
    
    # Системный промпт для ролевой игры
    system_prompt = f"""Ты - ролевой персонаж в Telegram-чате. Твоя задача:

1. Отвечай в стиле ролевой игры
2. Будь дружелюбным и интересным собеседником
3. Можешь использовать эмодзи
4. Ответы должны быть короткими и интересными
5. Поддерживай атмосферу ролевой игры

Пользователь: {user.first_name}"""
    
    # Вызов ИИ в отдельном потоке
    ai_response = await asyncio.to_thread(call_openrouter, user_message, system_prompt)
    
    # Проверяем, что ответ не пустой
    if not ai_response or ai_response.strip() == "":
        ai_response = "🤔 Мне нужно подумать... Попробуй спросить что-то ещё!"
    
    await update.message.reply_text(f"🤖 {ai_response}")

async def file_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда для генерации и отправки файла"""
    user = update.effective_user
    
    if not context.args:
        await update.message.reply_text(
            "📄 Команда для создания файлов через ИИ:\n\n"
            "📝 /file текст - создать текстовый файл\n"
            "📊 /file csv данные - создать CSV файл\n"
            "🗺 /file json данные - создать JSON файл\n"
            "📋 /file html страница - создать HTML файл\n\n"
            "💡 Примеры:\n"
            "/file Напиши стих о любви\n"
            "/file csv список продуктов и цен"
        )
        return
    
    # Определяем тип файла
    file_type = "txt"  # по умолчанию
    user_prompt = " ".join(context.args)
    
    # Проверяем, если первое слово - тип файла
    supported_types = ["txt", "csv", "json", "html", "py", "js", "css", "md", "xml"]
    if context.args[0].lower() in supported_types:
        file_type = context.args[0].lower()
        user_prompt = " ".join(context.args[1:])
        
        if not user_prompt:
            await update.message.reply_text(
                f"⚠️ Укажите описание для {file_type} файла!\n\n"
                f"💡 Пример: /file {file_type} создай пример кода"
            )
            return
    
    await update.message.reply_text(f"🤖 Создаю {file_type.upper()} файл... Подожди!")
    await update.message.chat.send_action("upload_document")
    
    try:
        # Генерируем содержимое файла
        content, filename = await asyncio.to_thread(generate_file_content, user_prompt, file_type)
        
        if not content or content.strip() == "":
            await update.message.reply_text(
                "😔 Не удалось создать файл. Попробуйте с другим описанием."
            )
            return
        
        # Создаём файл в памяти
        file_buffer = io.BytesIO(content.encode('utf-8'))
        file_buffer.name = filename
        
        # Отправляем файл
        await update.message.reply_document(
            document=file_buffer,
            filename=filename,
            caption=f"📄 Файл создан по запросу: {user_prompt[:50]}{'...' if len(user_prompt) > 50 else ''}"
        )
        
        logger.info(f"File generated for user {user.id}: {filename}")
        
    except Exception as e:
        logger.error(f"Error generating file: {e}")
        await update.message.reply_text(
            "❌ Ошибка при создании файла. Попробуйте позже."
        )

async def voice_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда для преобразования текста в голос"""
    user = update.effective_user
    
    if not context.args:
        await update.message.reply_text(
            "🎤 Команда для создания голосовых сообщений:\n\n"
            "🗣 /voice текст - русский голос\n"
            "🇬🇧 /voice en текст - английский голос\n"
            "🇪🇸 /voice es текст - испанский\n"
            "🇫🇷 /voice fr текст - французский\n\n"
            "💡 Примеры:\n"
            "/voice Привет, я РП бот!\n"
            "/voice en Hello, I am RP bot!\n"
            "\n⚠️ Максимум 200 символов"
        )
        return
    
    # Определяем язык
    language = "ru"  # по умолчанию
    text_to_convert = " ".join(context.args)
    
    # Проверяем, если первое слово - код языка
    supported_languages = {"ru", "en", "es", "fr", "de", "it", "pt", "ja", "ko", "zh"}
    if context.args[0].lower() in supported_languages:
        language = context.args[0].lower()
        text_to_convert = " ".join(context.args[1:])
        
        if not text_to_convert:
            await update.message.reply_text(
                f"⚠️ Укажите текст для произношения!\n\n"
                f"💡 Пример: /voice {language} Hello world!"
            )
            return
    
    # Проверка длины текста
    if len(text_to_convert) > 200:
        await update.message.reply_text(
            f"⚠️ Текст слишком длинный! ({len(text_to_convert)} символов)\n"
            "📊 Максимум: 200 символов"
        )
        return
    
    await update.message.reply_text(f"🎤 Создаю голосовое сообщение на {language.upper()}...")
    await update.message.chat.send_action("record_audio")
    
    try:
        # Генерируем голос
        audio_buffer = await asyncio.to_thread(text_to_speech, text_to_convert, language)
        
        if not audio_buffer:
            await update.message.reply_text(
                "❌ Не удалось создать голосовое сообщение. Попробуйте позже."
            )
            return
        
        # Отправляем голосовое сообщение
        await update.message.reply_voice(
            voice=audio_buffer,
            caption=f"🎤 Голос: {text_to_convert[:50]}{'...' if len(text_to_convert) > 50 else ''}"
        )
        
        logger.info(f"Voice message generated for user {user.id}: {language} - {text_to_convert[:50]}")
        
    except Exception as e:
        logger.error(f"Error generating voice message: {e}")
        await update.message.reply_text(
            "❌ Ошибка при создании голосового сообщения. Попробуйте позже."
        )

async def handle_ai_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка обычных сообщений как ИИ чат"""
    # Проверяем наличие сообщения и текста
    if not update.message or not update.message.text:
        return
        
    user = update.effective_user
    user_message = update.message.text
    
    # Проверяем, что это не команда
    if user_message.startswith('/'):
        return
    
    await update.message.chat.send_action("typing")
    
    # Системный промпт для обычного чата
    system_prompt = f"""Ты - ролевой персонаж в Telegram. Отвечай в стиле дружелюбного ролевого персонажа. Используй эмодзи, будь интересным собеседником. Ответы должны быть короткими.

Пользователь: {user.first_name}"""
    
    # Вызов ИИ в отдельном потоке
    ai_response = await asyncio.to_thread(call_openrouter, user_message, system_prompt)
    
    # Проверяем, что ответ не пустой
    if not ai_response or ai_response.strip() == "":
        ai_response = "🤔 Мне нужно подумать... Попробуй спросить что-то ещё!"
    
    await update.message.reply_text(ai_response)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда помощи"""
    help_text = """
📆 Помощь по боту

🎭 РП команды:
Используй /rp чтобы увидеть все команды

🤖 ИИ чат:
/ai сообщение - чат с ИИ
Или просто напиши мне сообщение!

📄 Создание файлов:
/file описание - создать TXT файл
/file csv данные - CSV таблица
/file json структура - JSON файл
/file html страница - HTML сайт

🎤 Голосовые сообщения:
/voice текст - русский голос
/voice en текст - английский
/voice es/fr/de текст - другие языки

👤 Профиль:
/profile - посмотреть свой профиль

💡 Примеры:
/hug @username
/kiss (ответом на сообщение)
/ai Привет! Как дела?
/file Напиши стих о любви
/file py скрипт для калькулятора
/voice Привет, я РП бот!
/voice en Hello, I am RP bot!
"""
    await update.message.reply_text(help_text)

def main():
    """Запуск бота"""
    # Создаем приложение напрямую с токеном из константы
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Регистрируем обработчики команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("profile", profile))
    application.add_handler(CommandHandler("rp", rp_commands))
    application.add_handler(CommandHandler("ai", ai_chat))
    application.add_handler(CommandHandler("file", file_command))
    application.add_handler(CommandHandler("voice", voice_command))
    application.add_handler(CommandHandler("help", help_command))
    
    # РП команды
    application.add_handler(CommandHandler("hug", hug))
    application.add_handler(CommandHandler("kiss", kiss))
    application.add_handler(CommandHandler("pat", pat))
    application.add_handler(CommandHandler("slap", slap))
    application.add_handler(CommandHandler("poke", poke))
    application.add_handler(CommandHandler("bite", bite))
    application.add_handler(CommandHandler("punch", punch))
    application.add_handler(CommandHandler("kill", kill))
    application.add_handler(CommandHandler("feed", feed))
    application.add_handler(CommandHandler("cuddle", cuddle))
    application.add_handler(CommandHandler("cry", cry))
    application.add_handler(CommandHandler("smile", smile))
    application.add_handler(CommandHandler("dance", dance))
    application.add_handler(CommandHandler("wave", wave))
    
    # Обработчик обычных сообщений для ИИ чата (должен быть последним!)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_ai_message))
    
    # Запускаем бота
    print("🤖 Бот с ИИ запущен!")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
