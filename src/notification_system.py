import asyncio
import time
from datetime import datetime, timedelta
import sys
import os

# Добавляем пути
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(os.path.dirname(__file__))

from database import get_tournaments_db, get_tournament_participants

# Импортируем настройки
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'config'))
from settings import BOT_TOKEN

# Для отправки сообщений через Telegram
import requests

def send_telegram_message(telegram_id, message):
    """Отправка сообщения в Telegram"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {
        'chat_id': telegram_id,
        'text': message,
        'parse_mode': 'HTML'
    }
    
    try:
        response = requests.post(url, data=data)
        return response.status_code == 200
    except Exception as e:
        print(f"Ошибка отправки сообщения: {e}")
        return False

def notify_participants_30min(tournament):
    """Уведомление за 30 минут до начала"""
    print(f"📢 Отправляем уведомления за 30 минут для турнира: {tournament['name']}")
    
    participants = get_tournament_participants(tournament['id'])
    
    for participant in participants:
        telegram_id = get_user_telegram_id(participant['username'])
        
        message = f"""🏆 <b>Напоминание о турнире!</b>

📅 Турнир "<b>{tournament['name']}</b>" начнется через 30 минут!

⏰ Время начала: {tournament['start_time']}
👥 Участников: {tournament['current_players']}

Не забудьте подготовиться! 🎮"""
        
        if telegram_id:
            success = send_telegram_message(telegram_id, message)
            print(f"  📱 Уведомление для {participant['username']}: {'✅ отправлено' if success else '❌ ошибка'}")
        else:
            print(f"  ❌ Не найден telegram_id для {participant['username']}")

def notify_participants_10min(tournament):
    """Уведомление за 10 минут до начала"""
    print(f"📢 Отправляем ЭКСТРЕННЫЕ уведомления за 10 минут для турнира: {tournament['name']}")
    
    participants = get_tournament_participants(tournament['id'])
    
    for participant in participants:
        telegram_id = get_user_telegram_id(participant['username'])
        
        message = f"""🚨 <b>ТУРНИР НАЧИНАЕТСЯ!</b>

🏆 Турнир "<b>{tournament['name']}</b>" начнется через 10 минут!

⏰ Время: {tournament['start_time']}
🎮 Заходите в игру и ждите коды лобби!

Удачи! 🍀"""
        
        if telegram_id:
            success = send_telegram_message(telegram_id, message)
            print(f"  🚨 ЭКСТРЕННОЕ уведомление для {participant['username']}: {'✅ отправлено' if success else '❌ ошибка'}")
        else:
            print(f"  ❌ Не найден telegram_id для {participant['username']}")

def get_user_telegram_id(username):
    """Получение telegram_id пользователя по username"""
    import sqlite3
    
    DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'garantgame.db')
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('SELECT telegram_id FROM users WHERE unique_username = ?', (username,))
    result = cursor.fetchone()
    conn.close()
    
    return result[0] if result else None

def check_tournaments_and_notify():
    """Проверка турниров и отправка уведомлений"""
    print("🔍 Проверяем турниры для уведомлений...")
    
    tournaments = get_tournaments_db()
    now = datetime.now()
    active_tournaments = 0
    
    for tournament in tournaments:
        if tournament['start_date'] and tournament['start_time']:
            # Создаем datetime начала турнира
            start_datetime = datetime.strptime(
                f"{tournament['start_date']} {tournament['start_time']}", 
                "%Y-%m-%d %H:%M"
            )
            
            time_until_start = start_datetime - now
            minutes_until_start = time_until_start.total_seconds() / 60
            
            # Пропускаем прошедшие турниры
            if minutes_until_start < 0:
                continue
            
            active_tournaments += 1
            print(f"⏰ Турнир '{tournament['name']}': до начала {int(minutes_until_start)} минут")
            
            # Проверяем нужно ли отправить уведомления
            if 29 <= minutes_until_start <= 31:
                print(f"📢 ОТПРАВЛЯЕМ уведомления за 30 минут!")
                notify_participants_30min(tournament)
                
            elif 9 <= minutes_until_start <= 11:
                print(f"🚨 ОТПРАВЛЯЕМ экстренные уведомления за 10 минут!")
                notify_participants_10min(tournament)
    
    if active_tournaments == 0:
        print("😴 Нет активных турниров для проверки")
    else:
        print(f"✅ Проверено {active_tournaments} активных турниров")

if __name__ == "__main__":
    print("🤖 Запуск системы уведомлений...")
    print("Нажмите Ctrl+C для остановки")
    
    try:
        while True:
            check_tournaments_and_notify()
            print("⏳ Ждем 1 минуту до следующей проверки...\n")
            time.sleep(60)  # Проверяем каждую минуту
    except KeyboardInterrupt:
        print("\n🛑 Система уведомлений остановлена")