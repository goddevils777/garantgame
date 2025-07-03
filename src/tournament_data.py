# Общее хранилище данных для бота и веба
tournaments = []

def add_tournament(name, min_players=10, max_players=16, creator_username="Веб", start_date=None, start_time=None, entry_fee=0):
    """Добавить новый турнир"""
    new_tournament = {
        'id': len(tournaments) + 1,
        'name': name,
        'min_players': int(min_players),
        'max_players': int(max_players),
        'current_players': 0,
        'status': 'Набор участников',
        'participants': [],
        'creator': creator_username,
        'start_date': start_date,
        'start_time': start_time,
        'entry_fee': float(entry_fee),
        'prize_pool': 0,
        'created_at': None
    }
    tournaments.append(new_tournament)
    return new_tournament

def delete_tournament(tournament_id, creator_username):
    """Удалить турнир (только создатель может удалить)"""
    global tournaments
    for i, tournament in enumerate(tournaments):
        if tournament['id'] == tournament_id and tournament['creator'] == creator_username:
            deleted_tournament = tournaments.pop(i)
            return True, f"Турнир '{deleted_tournament['name']}' удален"
    return False, "Турнир не найден или у вас нет прав на удаление"

def get_tournament_by_id(tournament_id):
    """Получить турнир по ID"""
    for tournament in tournaments:
        if tournament['id'] == tournament_id:
            return tournament
    return None

def get_tournaments():
    """Получить все турниры"""
    return tournaments

def join_tournament(tournament_id, username):
    """Присоединиться к турниру"""
    for tournament in tournaments:
        if tournament['id'] == tournament_id:
            if tournament['current_players'] < tournament['max_players']:
                if username not in tournament['participants']:
                    tournament['participants'].append(username)
                    tournament['current_players'] += 1
                    return True, f"Вы присоединились к турниру '{tournament['name']}'"
                else:
                    return False, "Вы уже участвуете в этом турнире"
            else:
                return False, "Турнир полный"
    return False, "Турнир не найден"

# Хранилище пользователей
users = {}

def create_user_profile(telegram_id, unique_username, first_name):
    """Создать профиль пользователя"""
    users[telegram_id] = {
        'telegram_id': telegram_id,
        'unique_username': unique_username,
        'first_name': first_name,
        'created_tournaments': 0,
        'joined_tournaments': 0
    }
    return users[telegram_id]

def get_user_by_telegram_id(telegram_id):
    """Получить пользователя по Telegram ID"""
    return users.get(telegram_id)

def is_username_taken(username):
    """Проверить, занят ли никнейм"""
    for user in users.values():
        if user['unique_username'].lower() == username.lower():
            return True
    return False

def get_all_usernames():
    """Получить все занятые никнеймы"""
    return [user['unique_username'] for user in users.values()]

def process_tournament_payment(tournament_id, username, payment_amount):
    """Обработать платеж за участие в турнире"""
    tournament = get_tournament_by_id(tournament_id)
    if not tournament:
        return False, "Турнир не найден"
    
    if tournament['entry_fee'] != payment_amount:
        return False, f"Неверная сумма оплаты. Требуется: ${tournament['entry_fee']}"
    
    # Здесь будет интеграция с платежной системой
    # Пока что просто имитируем успешную оплату
    tournament['prize_pool'] += payment_amount
    return True, f"Оплата ${payment_amount} успешно обработана"