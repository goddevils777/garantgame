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

def create_tournament_db(name, min_players, max_players, creator_username, start_date, start_time, entry_fee, tournament_type, tournament_password=None, prize_distribution_type='pyramid'):
    """Создать турнир в базе данных"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO tournaments (name, min_players, max_players, creator_username, 
                            start_date, start_time, entry_fee, tournament_type, tournament_password, prize_distribution_type)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (name, min_players, max_players, creator_username, start_date, start_time, entry_fee, tournament_type, tournament_password, prize_distribution_type))
    
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
                prize_pool, tournament_type, tournament_password, 
                prize_distribution_type, created_at
            FROM tournaments 
            ORDER BY created_at DESC
        ''')
    elif tournament_type == 'public':
        # Для неавторизованных - только публичные
        cursor.execute('''
            SELECT id, name, min_players, max_players, status, 
                creator_username, start_date, start_time, entry_fee, 
                prize_pool, tournament_type, tournament_password,
                prize_distribution_type, created_at
            FROM tournaments 
            WHERE tournament_type = 'public'
            ORDER BY created_at DESC
        ''')
    else:
        # ВСЕ турниры (включая приватные с паролем)
        cursor.execute('''
            SELECT id, name, min_players, max_players, status, 
                creator_username, start_date, start_time, entry_fee, 
                prize_pool, tournament_type, tournament_password,
                prize_distribution_type, created_at
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
            'prize_distribution_type': str(row[12]) if row[12] else 'pyramid',
            'created_at': str(row[13]) if row[13] else None,
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
            lobby_id, lobby_code, prize_distribution_type, created_at
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
        'prize_distribution_type': str(row[14]) if row[14] else 'pyramid',  # ← ДОБАВЬ ЭТУ СТРОКУ
        'created_at': str(row[15]) if row[15] else None,  # ← ОБРАТИ ВНИМАНИЕ: индекс увеличился на 1
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

        # Добавляем поле для PUBG никнейма
        try:
            cursor.execute('ALTER TABLE users ADD COLUMN pubg_nickname TEXT DEFAULT ""')
        except sqlite3.OperationalError:
            pass  # Поле уже существует
        
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
    """Рассчитать распределение призов по ТОЧНОЙ таблице 1 в 1"""
    if entry_fee <= 0 or max_players <= 0:
        return {
            'total_pool': 0,
            'our_commission': 0,
            'prize_pool': 0,
            'distribution': [],
            'prize_places': 0
        }
    
    # Основные расчеты
    total_pool = max_players * entry_fee
    our_commission = total_pool * 0.05  # 5% комиссия
    prize_pool = total_pool - our_commission
    
    # ПОЛНАЯ ТОЧНАЯ таблица из CSV файла
    exact_percentages = {
        10: [60.45, 34.55],
        11: [60.45, 34.55],
        12: [60.46, 34.54],
        13: [60.45, 34.55],
        14: [60.46, 34.54],
        15: [51.15, 29.23, 14.61],
        16: [51.16, 29.23, 14.61],
        17: [51.15, 29.23, 14.62],
        18: [51.16, 29.23, 14.61],
        19: [51.15, 29.23, 14.62],
        20: [47.5, 27.15, 13.57, 6.79],
        25: [44.33, 25.33, 12.67, 6.34, 6.33],
        30: [43.18, 24.68, 12.34, 6.17, 6.17, 2.46],
        35: [42.09, 24.05, 12.03, 6.01, 6.01, 2.41, 2.41],
        40: [41.05, 23.46, 11.73, 5.86, 5.86, 2.35, 2.35, 2.35],
        45: [40.06, 22.89, 11.45, 5.72, 5.72, 2.29, 2.29, 2.29, 2.29],
        50: [39.12, 22.35, 11.18, 5.59, 5.59, 2.23, 2.24, 2.24, 2.24, 2.24],
        55: [38.66, 22.09, 11.05, 5.52, 5.52, 2.21, 2.21, 2.21, 2.21, 2.21, 1.1],
        60: [38.22, 21.84, 10.92, 5.46, 5.46, 2.18, 2.18, 2.18, 2.18, 2.18, 1.1, 1.09],
        65: [37.78, 21.59, 10.8, 5.4, 5.4, 2.16, 2.16, 2.16, 2.16, 2.16, 1.08, 1.08, 1.08],
        70: [37.36, 21.35, 10.67, 5.34, 5.34, 2.13, 2.13, 2.13, 2.13, 2.13, 1.07, 1.07, 1.07, 1.07],
        75: [36.94, 21.11, 10.56, 5.28, 5.28, 2.11, 2.11, 2.11, 2.11, 2.11, 1.06, 1.06, 1.06, 1.06, 1.06],
        80: [36.54, 20.88, 10.44, 5.22, 5.22, 2.09, 2.09, 2.09, 2.09, 2.09, 1.05, 1.04, 1.04, 1.04, 1.04, 1.04],
        85: [36.14, 20.65, 10.33, 5.16, 5.16, 2.06, 2.06, 2.06, 2.06, 2.06, 1.03, 1.03, 1.03, 1.03, 1.03, 1.03, 1.03],
        90: [35.75, 20.43, 10.22, 5.11, 5.11, 2.04, 2.04, 2.04, 2.04, 2.04, 1.02, 1.02, 1.02, 1.02, 1.02, 1.02, 1.02, 1.02],
        95: [35.37, 20.21, 10.11, 5.05, 5.05, 2.02, 2.02, 2.02, 2.02, 2.02, 1.01, 1.01, 1.01, 1.01, 1.01, 1.01, 1.01, 1.01, 1.01],
        100: [35, 20, 10, 5, 5, 2, 2, 2, 2, 2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
    }
    
    # Количество призовых мест (20% от участников, минимум 2)
    prize_places = max(2, int(max_players * 0.2))
    
    distribution = []
    
    if distribution_type == 'pyramid':
        # PYRAMID стратегия - получаем точные проценты из первой таблицы
        if max_players in exact_percentages:
            percentages = exact_percentages[max_players]
        else:
            # Находим ближайшее значение для pyramid
            available_counts = list(exact_percentages.keys())
            closest = min(available_counts, key=lambda x: abs(x - max_players))
            percentages = exact_percentages[closest]
        
        # Создаем распределение для PYRAMID
        for i in range(min(prize_places, len(percentages))):
            percentage = percentages[i]
            amount = round(total_pool * (percentage / 100), 2)
            
            distribution.append({
                'place': i + 1,
                'percentage': percentage,
                'amount': amount
            })
    
    elif distribution_type == 'nonlinear':
        # NON-LINEAR стратегия - получаем проценты из второй таблицы
        if max_players in nonlinear_percentages:
            percentages = nonlinear_percentages[max_players]
        else:
            # Находим ближайшее значение для non-linear
            available_counts = list(nonlinear_percentages.keys())
            closest = min(available_counts, key=lambda x: abs(x - max_players))
            percentages = nonlinear_percentages[closest]
        
        # Создаем распределение для NON-LINEAR
        for i in range(min(prize_places, len(percentages))):
            percentage = percentages[i]
            amount = round(total_pool * (percentage / 100), 2)
            
            distribution.append({
                'place': i + 1,
                'percentage': percentage,
                'amount': amount
            })
    
    return {
        'total_pool': round(total_pool, 2),
        'our_commission': round(our_commission, 2),
        'prize_pool': round(prize_pool, 2),
        'distribution': distribution,
        'prize_places': prize_places
    }

def update_user_pubg_nickname(telegram_id, pubg_nickname):
    """Обновить PUBG никнейм пользователя"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            UPDATE users 
            SET pubg_nickname = ?
            WHERE telegram_id = ?
        ''', (pubg_nickname, telegram_id))
        
        conn.commit()
        return cursor.rowcount > 0
    except Exception as e:
        print(f"Ошибка обновления PUBG никнейма: {e}")
        return False
    finally:
        conn.close()

def get_tournament_participants_with_pubg(tournament_id):
    """Получить участников турнира с их PUBG никнеймами"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT tp.username, tp.joined_at, u.pubg_nickname
        FROM tournament_participants tp
        JOIN users u ON tp.username = u.unique_username
        WHERE tp.tournament_id = ?
        ORDER BY tp.joined_at ASC
    ''', (tournament_id,))
    
    participants = []
    for row in cursor.fetchall():
        participants.append({
            'username': row[0],
            'joined_at': row[1],
            'pubg_nickname': row[2] if row[2] else ''
        })
    
    conn.close()
    return participants

# Инициализация базы данных при импорте
if __name__ == "__main__":
    init_database()
else:
    init_database()