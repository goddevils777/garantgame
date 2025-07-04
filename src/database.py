import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'garantgame.db')

def init_database():
    """Инициализация базы данных"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Таблица пользователей с балансом
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER UNIQUE NOT NULL,
                unique_username TEXT UNIQUE NOT NULL,
                first_name TEXT NOT NULL,
                last_name TEXT DEFAULT '',
                photo_url TEXT DEFAULT '',
                balance REAL DEFAULT 0.0,
                pubg_nickname TEXT DEFAULT '',
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
            
        try:
            cursor.execute('ALTER TABLE users ADD COLUMN balance REAL DEFAULT 0.0')
        except sqlite3.OperationalError:
            pass
            
        try:
            cursor.execute('ALTER TABLE users ADD COLUMN pubg_nickname TEXT DEFAULT ""')
        except sqlite3.OperationalError:
            pass
        
        # Таблица турниров
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
        
        # Добавляем новые столбцы к турнирам (если их нет)
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
            
        try:
            cursor.execute('ALTER TABLE tournaments ADD COLUMN prize_distribution_type TEXT DEFAULT "pyramid"')
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
        
        # Таблица транзакций
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                tournament_id INTEGER,
                transaction_type TEXT NOT NULL,
                amount REAL NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (tournament_id) REFERENCES tournaments (id)
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
            'balance': user[6] if len(user) > 6 else 0.0,
            'pubg_nickname': user[7] if len(user) > 7 else '',
            'created_at': user[8] if len(user) > 8 else '',
            'created_tournaments': user[9] if len(user) > 9 else 0,
            'joined_tournaments': user[10] if len(user) > 10 else 0
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
        cursor.execute('''
            SELECT id, name, min_players, max_players, status, 
                creator_username, start_date, start_time, entry_fee, 
                prize_pool, tournament_type, tournament_password, 
                prize_distribution_type, created_at
            FROM tournaments 
            ORDER BY created_at DESC
        ''')
    elif tournament_type == 'public':
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
        cursor.execute('DELETE FROM tournament_participants WHERE tournament_id = ?', (tournament_id,))
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
        return cursor.rowcount > 0
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
        return cursor.rowcount > 0
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
            'prize_distribution_type': str(row[14]) if row[14] else 'pyramid',
            'created_at': str(row[15]) if row[15] else None,
            'current_players': participants_count,
            'participants': []
        }
    return None

def calculate_prize_distribution(max_players, entry_fee, distribution_type='pyramid'):
    """Рассчитать распределение призов"""
    if entry_fee <= 0 or max_players <= 0:
        return {
            'total_pool': 0,
            'our_commission': 0,
            'prize_pool': 0,
            'distribution': [],
            'prize_places': 0
        }
    
    total_pool = max_players * entry_fee
    our_commission = total_pool * 0.05
    prize_pool = total_pool - our_commission
    
    exact_percentages = {
        10: [60.45, 34.55],
        20: [47.5, 27.15, 13.57, 6.79],
        50: [39.12, 22.35, 11.18, 5.59, 5.59, 2.23, 2.24, 2.24, 2.24, 2.24],
        100: [35, 20, 10, 5, 5, 2, 2, 2, 2, 2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
    }
    
    prize_places = max(2, int(max_players * 0.2))
    
    if max_players in exact_percentages:
        percentages = exact_percentages[max_players]
    else:
        available_counts = list(exact_percentages.keys())
        closest = min(available_counts, key=lambda x: abs(x - max_players))
        percentages = exact_percentages[closest]
    
    distribution = []
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

def get_user_balance(telegram_id):
    """Получить баланс пользователя"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('SELECT balance FROM users WHERE telegram_id = ?', (telegram_id,))
    result = cursor.fetchone()
    conn.close()
    
    return result[0] if result else 0.0

def update_user_balance(telegram_id, new_balance):
    """Обновить баланс пользователя"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute('UPDATE users SET balance = ? WHERE telegram_id = ?', (new_balance, telegram_id))
        conn.commit()
        return cursor.rowcount > 0
    except Exception as e:
        print(f"Ошибка обновления баланса: {e}")
        return False
    finally:
        conn.close()

def add_transaction(telegram_id, transaction_type, amount, description, tournament_id=None):
    """Добавить транзакцию"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute('SELECT id FROM users WHERE telegram_id = ?', (telegram_id,))
        user_result = cursor.fetchone()
        
        if not user_result:
            return False
            
        user_id = user_result[0]
        
        cursor.execute('''
            INSERT INTO transactions (user_id, tournament_id, transaction_type, amount, description)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, tournament_id, transaction_type, amount, description))
        
        conn.commit()
        return True
    except Exception as e:
        print(f"Ошибка добавления транзакции: {e}")
        return False
    finally:
        conn.close()

def process_tournament_payment_from_balance(telegram_id, tournament_id, username, amount):
    """Списать с баланса за участие в турнире"""
    current_balance = get_user_balance(telegram_id)
    
    if current_balance < amount:
        return False, f"Недостаточно средств. Баланс: ${current_balance:.2f}, требуется: ${amount:.2f}"
    
    new_balance = current_balance - amount
    
    if update_user_balance(telegram_id, new_balance):
        add_transaction(telegram_id, 'tournament_payment', -amount, f'Участие в турнире ID:{tournament_id}', tournament_id)
        
        success = add_tournament_participant(tournament_id, username)
        
        if success:
            return True, f"Оплата ${amount:.2f} прошла успешно. Остаток: ${new_balance:.2f}"
        else:
            update_user_balance(telegram_id, current_balance)
            return False, "Ошибка добавления в турнир"
    else:
        return False, "Ошибка списания с баланса"

# Инициализация базы данных при импорте
if __name__ == "__main__":
    init_database()
else:
    init_database()