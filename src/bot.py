import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import sys
import os
import time
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from urllib.parse import quote
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from urllib.parse import unquote

# Добавляем путь к config
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from config.settings import BOT_TOKEN, BOT_NAME

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Добавь эту функцию в bot.py
async def auth_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка команды /start auth для авторизации"""
    user = update.effective_user
    user_id = user.id
    username = user.username or ""
    first_name = user.first_name
    last_name = user.last_name or ""
    
    print(f"🔍 Начинаем авторизацию для пользователя: {first_name} (ID: {user_id})")
    
    # Получение аватарки с правильным формированием ссылки
    photo_url = ""
    try:
        print("📸 Пытаемся получить фото профиля...")
        user_profile_photos = await context.bot.get_user_profile_photos(user_id, limit=1)
        print(f"📊 Количество фото: {user_profile_photos.total_count}")
        
        if user_profile_photos.total_count > 0:
            print("✅ Фото найдено, получаем файл...")
            largest_photo = user_profile_photos.photos[0][-1]
            print(f"📋 File ID: {largest_photo.file_id}")
            
            file_info = await context.bot.get_file(largest_photo.file_id)
            print(f"📂 File path from API: {file_info.file_path}")
            
            # ИСПРАВЛЕНИЕ: file_info.file_path уже содержит только путь к файлу
            photo_url = file_info.file_path
            print(f"🔗 Итоговая ссылка: {photo_url}")
        else:
            print("❌ У пользователя нет фото профиля")
    except Exception as e:
        print(f"🚨 ОШИБКА получения аватарки: {e}")
        import traceback
        traceback.print_exc()
    
    # Создаем ссылку
    current_time = int(time.time())
    auth_params = f"id={user_id}&first_name={first_name}&last_name={last_name}&username={username}&photo_url={photo_url}&auth_date={current_time}"
    
    print(f"🌐 Параметры авторизации: {auth_params}")
    
    # ЗАМЕНИ НА СВОЮ NGROK ССЫЛКУ
    auth_url = f"https://a771-2a09-bac5-596c-52d-00-84-98.ngrok-free.app/auth/telegram?{auth_params}"
    
    welcome_message = f"""
🎮 Добро пожаловать в GarantGame!

Привет, {first_name}! 

Для завершения входа на сайт нажмите кнопку ниже:

⚠️ Ссылка действительна 10 минут.
    """
    
    keyboard = [
        [InlineKeyboardButton("🔗 Завершить вход на сайт", url=auth_url)]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(welcome_message, reply_markup=reply_markup)

# Обнови функцию start для обработки параметра auth
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start"""
    # Проверяем, есть ли параметр auth
    if context.args and context.args[0] == 'auth':
        await auth_start(update, context)
        return
    
    await update.message.reply_text(
        f"Привет! Это {BOT_NAME} - бот для управления турнирами!\n"
        f"Используй /help для списка команд."
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /help"""
    help_text = """
🎮 GarantGame - Турнирный бот

Доступные команды:
/start - Начать работу с ботом
/help - Показать это сообщение  
/create_tournament - Создать новый турнир
/join_tournament - Присоединиться к турниру
"""
    await update.message.reply_text(help_text)


async def create_tournament(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /create_tournament"""
    user_id = update.effective_user.id
    username = update.effective_user.username or "Без имени"
    
    # Простая заглушка для турнира
    tournament_info = f"""
🏆 Турнир создан!

👤 Создатель: @{username}
🆔 ID турнира: TOUR_{user_id}_{len(str(user_id))}
⏰ Создан: только что

Статус: Набор участников
Участников: 1/8

Используй /join_tournament для участия в турнире
    """
    
    await update.message.reply_text(tournament_info)

def main():
    """Запуск бота"""
    # Создаем приложение
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Добавляем обработчики команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    
    print(f"🤖 {BOT_NAME} запущен!")
    
    # Запускаем бота
    application.run_polling()

if __name__ == '__main__':
    main()