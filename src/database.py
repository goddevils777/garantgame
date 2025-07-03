import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'garantgame.db')

def init_database():
    """Инициализация базы данных"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Таблица пользователей
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER UNIQUE NOT NULL,
                unique_username TEXT UNIQUE NOT NULL,
                first_name TEXT NOT NULL,
                last_name TEXT DEFAULT '',
                photo_url TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_tournaments INTEGER DEFAULT 0,
                joined_tournaments INTEGER DEFAULT 0
            )
        ''')
        
        # Добавляем новые столбцы к существующей таблице (если их нет)
        try:
            cursor.execute('ALTER TABLE users ADD COLUMN last_name TEXT DEFAULT ""')
        except sqlite3.OperationalError:
            pass
        
        try:
            cursor.execute('ALTER TABLE users ADD COLUMN photo_url TEXT DEFAULT ""')
        except sqlite3.OperationalError:
            pass
        
        # Таблица турниров с кодами лобби
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tournaments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                min_players INTEGER NOT NULL,
                max_players INTEGER NOT NULL,
                current_players INTEGER DEFAULT 0,
                status TEXT DEFAULT 'Набор участников',
                creator_username TEXT NOT NULL,
                start_date TEXT,
                start_time TEXT,
                entry_fee REAL DEFAULT 0,
                prize_pool REAL DEFAULT 0,
                tournament_type TEXT DEFAULT 'public',
                tournament_password TEXT,
                lobby_id TEXT,
                lobby_code TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (creator_username) REFERENCES users (unique_username)
            )
        ''')
        
        # Добавляем новые столбцы к существующей таблице (если их нет)
        try:
            cursor.execute('ALTER TABLE tournaments ADD COLUMN tournament_password TEXT')
        except sqlite3.OperationalError:
            pass
            
        try:
            cursor.execute('ALTER TABLE tournaments ADD COLUMN lobby_id TEXT')
        except sqlite3.OperationalError:
            pass
            
        try:
            cursor.execute('ALTER TABLE tournaments ADD COLUMN lobby_code TEXT')
        except sqlite3.OperationalError:
            pass
        
        # Таблица участников турниров
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tournament_participants (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tournament_id INTEGER NOT NULL,
                username TEXT NOT NULL,
                joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                payment_status TEXT DEFAULT 'pending',
                FOREIGN KEY (tournament_id) REFERENCES tournaments (id),
                FOREIGN KEY (username) REFERENCES users (unique_username),
                UNIQUE(tournament_id, username)
            )
        ''')
        
        conn.commit()
        print("✅ База данных инициализирована успешно")
        
    except Exception as e:
        print(f"❌ Ошибка инициализации базы данных: {e}")
        conn.rollback()
    finally:
        conn.close()

def create_user_db(telegram_id, unique_username, first_name, last_name="", photo_url=""):
    """Создать пользователя в базе данных"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT INTO users (telegram_id, unique_username, first_name, last_name, photo_url)
            VALUES (?, ?, ?, ?, ?)
        ''', (telegram_id, unique_username, first_name, last_name, photo_url))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def get_user_by_telegram_id_db(telegram_id):
    """Получить пользователя по Telegram ID"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM users WHERE telegram_id = ?', (telegram_id,))
    user = cursor.fetchone()
    conn.close()
    
    if user:
        return {
            'id': user[0],
            'telegram_id': user[1],
            'unique_username': user[2],
            'first_name': user[3],
            'last_name': user[4] if len(user) > 4 else '',
            'photo_url': user[5] if len(user) > 5 else '',
            'created_at': user[6] if len(user) > 6 else '',
            'created_tournaments': user[7] if len(user) > 7 else 0,
            'joined_tournaments': user[8] if len(user) > 8 else 0
        }
    return None

def get_user_by_telegram_id_db(telegram_id):
    """Получить пользователя по Telegram ID"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM users WHERE telegram_id = ?', (telegram_id,))
    user = cursor.fetchone()
    conn.close()
    
    if user:
        return {
            'id': user[0],
            'telegram_id': user[1],
            'unique_username': user[2],
            'first_name': user[3],
            'created_at': user[4],
            'created_tournaments': user[5],
            'joined_tournaments': user[6]
        }
    return None

def is_username_taken_db(username):
    """Проверить, занят ли никнейм в базе данных"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('SELECT COUNT(*) FROM users WHERE unique_username = ?', (username,))
    count = cursor.fetchone()[0]
    conn.close()
    
    return count > 0

def create_tournament_db(name, min_players, max_players, creator_username, start_date, start_time, entry_fee, tournament_type, tournament_password=None):
    """Создать турнир в базе данных"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO tournaments (name, min_players, max_players, creator_username, 
                               start_date, start_time, entry_fee, tournament_type, tournament_password)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (name, min_players, max_players, creator_username, start_date, start_time, entry_fee, tournament_type, tournament_password))
    
    tournament_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return tournament_id

def get_tournaments_db(tournament_type=None, user_username=None):
    """Получить турниры из базы данных"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    if user_username:
        # Для авторизованных пользователей - показать ВСЕ турниры (публичные + все приватные)
        cursor.execute('''
            SELECT id, name, min_players, max_players, status, 
                   creator_username, start_date, start_time, entry_fee, 
                   prize_pool, tournament_type, tournament_password, created_at
            FROM tournaments 
            ORDER BY created_at DESC
        ''')
    elif tournament_type == 'public':
        # Для неавторизованных - только публичные
        cursor.execute('''
            SELECT id, name, min_players, max_players, status, 
                   creator_username, start_date, start_time, entry_fee, 
                   prize_pool, tournament_type, tournament_password, created_at
            FROM tournaments 
            WHERE tournament_type = 'public'
            ORDER BY created_at DESC
        ''')
    else:
        # ВСЕ турниры (включая приватные с паролем)
        cursor.execute('''
            SELECT id, name, min_players, max_players, status, 
                   creator_username, start_date, start_time, entry_fee, 
                   prize_pool, tournament_type, tournament_password, created_at
            FROM tournaments 
            ORDER BY created_at DESC
        ''')
    
    tournaments = []
    for row in cursor.fetchall():
        tournament_id = row[0]
        
        # Получаем количество участников отдельным запросом
        cursor.execute('SELECT COUNT(*) FROM tournament_participants WHERE tournament_id = ?', (tournament_id,))
        participants_count = cursor.fetchone()[0]
        
        tournaments.append({
            'id': int(row[0]),                                    # 0
            'name': str(row[1]),                                  # 1
            'min_players': int(row[2]),                           # 2
            'max_players': int(row[3]),                           # 3
            'status': str(row[4]),                                # 4
            'creator': str(row[5]),                               # 5
            'start_date': str(row[6]) if row[6] else None,        # 6
            'start_time': str(row[7]) if row[7] else None,        # 7
            'entry_fee': float(row[8]) if row[8] else 0.0,        # 8
            'prize_pool': float(row[9]) if row[9] else 0.0,       # 9
            'tournament_type': str(row[10]),                      # 10
            'tournament_password': str(row[11]) if row[11] else None,  # 11
            'created_at': str(row[12]) if row[12] else None,      # 12
            'current_players': int(participants_count),
            'participants': []
        })
    
    conn.close()
    return tournaments

def get_tournament_participants(tournament_id):
    """Получить участников турнира"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT username, joined_at 
        FROM tournament_participants 
        WHERE tournament_id = ?
        ORDER BY joined_at ASC
    ''', (tournament_id,))
    
    participants = []
    for row in cursor.fetchall():
        participants.append({
            'username': row[0],
            'joined_at': row[1]
        })
    
    conn.close()
    return participants

def add_tournament_participant(tournament_id, username):
    """Добавить участника в турнир"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT INTO tournament_participants (tournament_id, username)
            VALUES (?, ?)
        ''', (tournament_id, username))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        # Пользователь уже участвует
        return False
    except Exception as e:
        print(f"Ошибка добавления участника: {e}")
        return False
    finally:
        conn.close()

def delete_tournament_db(tournament_id):
    """Удалить турнир и всех его участников"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Удаляем участников турнира
        cursor.execute('DELETE FROM tournament_participants WHERE tournament_id = ?', (tournament_id,))
        # Удаляем турнир
        cursor.execute('DELETE FROM tournaments WHERE id = ?', (tournament_id,))
        conn.commit()
        return True
    except Exception as e:
        print(f"Ошибка удаления турнира: {e}")
        return False
    finally:
        conn.close()


def update_tournament_db(tournament_id, min_players, max_players, entry_fee, start_date, start_time):
    """Обновить турнир в базе данных"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            UPDATE tournaments 
            SET min_players = ?, max_players = ?, entry_fee = ?, start_date = ?, start_time = ?
            WHERE id = ?
        ''', (min_players, max_players, entry_fee, start_date, start_time, tournament_id))
        
        conn.commit()
        return cursor.rowcount > 0  # Возвращает True, если обновлена хотя бы одна строка
    except Exception as e:
        print(f"Ошибка обновления турнира: {e}")
        return False
    finally:
        conn.close()

def update_tournament_password_db(tournament_id, new_password):
    """Обновить пароль турнира в базе данных"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            UPDATE tournaments 
            SET tournament_password = ?
            WHERE id = ? AND tournament_type = 'private'
        ''', (new_password, tournament_id))
        
        conn.commit()
        return cursor.rowcount > 0  # Возвращает True, если обновлена хотя бы одна строка
    except Exception as e:
        print(f"Ошибка обновления пароля турнира: {e}")
        return False
    finally:
        conn.close()

def update_lobby_codes_db(tournament_id, lobby_id, lobby_code):
    """Обновить коды лобби турнира в базе данных"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            UPDATE tournaments 
            SET lobby_id = ?, lobby_code = ?
            WHERE id = ?
        ''', (lobby_id, lobby_code, tournament_id))
        
        conn.commit()
        return cursor.rowcount > 0
    except Exception as e:
        print(f"Ошибка обновления кодов лобби: {e}")
        return False
    finally:
        conn.close()

def get_tournament_with_lobby_db(tournament_id):
    """Получить турнир с кодами лобби"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, name, min_players, max_players, status, 
               creator_username, start_date, start_time, entry_fee, 
               prize_pool, tournament_type, tournament_password, 
               lobby_id, lobby_code, created_at
        FROM tournaments 
        WHERE id = ?
    ''', (tournament_id,))
    
    row = cursor.fetchone()
    conn.close()
    
    if row:
        # Получаем количество участников
        participants_count = len(get_tournament_participants(tournament_id))
        
        return {
            'id': int(row[0]),
            'name': str(row[1]),
            'min_players': int(row[2]),
            'max_players': int(row[3]),
            'status': str(row[4]),
            'creator': str(row[5]),
            'start_date': str(row[6]) if row[6] else None,
            'start_time': str(row[7]) if row[7] else None,
            'entry_fee': float(row[8]) if row[8] else 0.0,
            'prize_pool': float(row[9]) if row[9] else 0.0,
            'tournament_type': str(row[10]),
            'tournament_password': str(row[11]) if row[11] else None,
            'lobby_id': str(row[12]) if row[12] else None,
            'lobby_code': str(row[13]) if row[13] else None,
            'created_at': str(row[14]) if row[14] else None,
            'current_players': participants_count,
            'participants': []
        }
    return None

def init_database():
    """Инициализация базы данных"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Таблица пользователей (без изменений)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER UNIQUE NOT NULL,
                unique_username TEXT UNIQUE NOT NULL,
                first_name TEXT NOT NULL,
                last_name TEXT DEFAULT '',
                photo_url TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_tournaments INTEGER DEFAULT 0,
                joined_tournaments INTEGER DEFAULT 0
            )
        ''')
        
        # Добавляем новые столбцы к существующей таблице пользователей
        try:
            cursor.execute('ALTER TABLE users ADD COLUMN last_name TEXT DEFAULT ""')
        except sqlite3.OperationalError:
            pass
        
        try:
            cursor.execute('ALTER TABLE users ADD COLUMN photo_url TEXT DEFAULT ""')
        except sqlite3.OperationalError:
            pass
        
        # Таблица турниров с системой призов
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tournaments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                min_players INTEGER NOT NULL,
                max_players INTEGER NOT NULL,
                current_players INTEGER DEFAULT 0,
                status TEXT DEFAULT 'Набор участников',
                creator_username TEXT NOT NULL,
                start_date TEXT,
                start_time TEXT,
                entry_fee REAL DEFAULT 0,
                prize_pool REAL DEFAULT 0,
                tournament_type TEXT DEFAULT 'public',
                tournament_password TEXT,
                lobby_id TEXT,
                lobby_code TEXT,
                prize_distribution_type TEXT DEFAULT 'pyramid',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (creator_username) REFERENCES users (unique_username)
            )
        ''')
        
        # Добавляем новые столбцы к существующей таблице турниров
        existing_columns = [
            ('tournament_password', 'TEXT'),
            ('lobby_id', 'TEXT'),
            ('lobby_code', 'TEXT'),
            ('prize_distribution_type', 'TEXT DEFAULT "pyramid"')
        ]
        
        for column_name, column_type in existing_columns:
            try:
                cursor.execute(f'ALTER TABLE tournaments ADD COLUMN {column_name} {column_type}')
            except sqlite3.OperationalError:
                pass
        
        # Таблица участников (без изменений)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tournament_participants (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tournament_id INTEGER NOT NULL,
                username TEXT NOT NULL,
                joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                payment_status TEXT DEFAULT 'pending',
                FOREIGN KEY (tournament_id) REFERENCES tournaments (id),
                FOREIGN KEY (username) REFERENCES users (unique_username),
                UNIQUE(tournament_id, username)
            )
        ''')
        
        conn.commit()
        print("✅ База данных инициализирована успешно")
        
    except Exception as e:
        print(f"❌ Ошибка инициализации базы данных: {e}")
        conn.rollback()
    finally:
        conn.close()

def calculate_prize_distribution(max_players, entry_fee, distribution_type='pyramid'):
    """Рассчитать распределение призов"""
    if entry_fee <= 0 or max_players <= 0:
        return {
            'total_pool': 0,
            'our_commission': 0,
            'prize_pool': 0,
            'distribution': []
        }
    
    total_pool = max_players * entry_fee
    our_commission = total_pool * 0.05  # 5% комиссия
    prize_pool = total_pool - our_commission
    
    # Количество призовых мест (максимум 20, но не больше участников)
    prize_places = min(20, max_players)
    
    distribution = []
    
    if distribution_type == 'pyramid':
        # Классическая "Пирамида"
        percentages = {
            1: 40,    # 1 место: 40%
            2: 20,    # 2 место: 20%
            3: 12,    # 3 место: 12%
        }
        
        # 4-5 места: 10% всего (по 5% каждому)
        for place in [4, 5]:
            if place <= prize_places:
                percentages[place] = 5
        
        # 6-10 места: 10% всего (по 2% каждому)
        places_6_10 = [p for p in range(6, 11) if p <= prize_places]
        if places_6_10:
            percent_per_place = 10 / len(places_6_10)
            for place in places_6_10:
                percentages[place] = percent_per_place
        
        # 11-20 места: 10% всего
        places_11_20 = [p for p in range(11, 21) if p <= prize_places]
        if places_11_20:
            percent_per_place = 10 / len(places_11_20)
            for place in places_11_20:
                percentages[place] = percent_per_place
        
        # Создаем распределение
        for place in range(1, prize_places + 1):
            percent = percentages.get(place, 0)
            amount = (prize_pool * percent) / 100
            distribution.append({
                'place': place,
                'percentage': percent,
                'amount': round(amount, 2)
            })
    
    else:  # non-linear
        # Non-linear распределение
        percentages = {}
        
        if prize_places >= 1:
            percentages[1] = 18  # 1 место: 18%
        if prize_places >= 2:
            percentages[2] = 13  # 2 место: 13%
        if prize_places >= 3:
            percentages[3] = 10  # 3 место: 10%
        
        # 4-10 места: 35% всего
        places_4_10 = [p for p in range(4, 11) if p <= prize_places]
        if places_4_10:
            percent_per_place = 35 / len(places_4_10)
            for place in places_4_10:
                percentages[place] = percent_per_place
        
        # 11-20 места: 24% всего
        places_11_20 = [p for p in range(11, 21) if p <= prize_places]
        if places_11_20:
            percent_per_place = 24 / len(places_11_20)
            for place in places_11_20:
                percentages[place] = percent_per_place
        
        # Создаем распределение
        for place in range(1, prize_places + 1):
            percent = percentages.get(place, 0)
            amount = (prize_pool * percent) / 100
            distribution.append({
                'place': place,
                'percentage': percent,
                'amount': round(amount, 2)
            })
    
    return {
        'total_pool': round(total_pool, 2),
        'our_commission': round(our_commission, 2),
        'prize_pool': round(prize_pool, 2),
        'distribution': distribution,
        'prize_places': prize_places
    }

# Инициализация базы данных при импорте
if __name__ == "__main__":
    init_database()
else:
    init_database()