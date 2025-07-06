from flask import Flask, render_template, request, redirect, url_for, flash, session
import sys
import os
import re
import time
from urllib.parse import unquote

# Добавляем пути
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from config.settings import BOT_NAME, BOT_TOKEN
from auth import verify_telegram_auth, create_telegram_login_widget
from database import (create_user_db, get_user_by_telegram_id_db, is_username_taken_db,
                     create_tournament_db, get_tournaments_db, get_tournament_participants,
                     add_tournament_participant, delete_tournament_db, update_tournament_db,
                     update_tournament_password_db, update_lobby_codes_db, get_tournament_with_lobby_db,
                     calculate_prize_distribution, get_user_balance, update_user_balance, 
                     add_transaction, process_tournament_payment_from_balance)

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'

# Получаем username бота для виджета
BOT_USERNAME = "garantgameproject_bot"  # ЗАМЕНИ НА РЕАЛЬНЫЙ USERNAME БОТА

def send_lobby_codes_notifications(tournament_id, tournament_name, lobby_id, lobby_code):
    """Отправка уведомлений о кодах лобби всем участникам"""
    try:
        import requests
        from config.settings import BOT_TOKEN
        
        # Получаем участников
        participants = get_tournament_participants(tournament_id)
        
        for participant in participants:
            # Получаем пользователя по username
            import sqlite3
            DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'garantgame.db')
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            cursor.execute('SELECT telegram_id FROM users WHERE unique_username = ?', (participant['username'],))
            result = cursor.fetchone()
            conn.close()
            
            if not result:
                print(f"❌ Не найден telegram_id для {participant['username']}")
                continue
                
            telegram_id = result[0]
            
            codes_text = ""
            if lobby_id:
                codes_text += f"🆔 <b>ID Лобби:</b> <code>{lobby_id}</code>\n"
            if lobby_code:
                codes_text += f"🔑 <b>Код Лобби:</b> <code>{lobby_code}</code>\n"
            
            message = f"""🎮 <b>КОДЫ ЛОББИ ВЫДАНЫ!</b>

🏆 Турнир: <b>{tournament_name}</b>

{codes_text}
Заходите в игру! Удачи! 🍀"""
            
            # Отправляем уведомление
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
            data = {
                'chat_id': telegram_id,
                'text': message,
                'parse_mode': 'HTML'
            }
            
            response = requests.post(url, data=data)
            if response.status_code == 200:
                print(f"✅ Коды лобби отправлены участнику: {participant['username']}")
            else:
                print(f"❌ Ошибка отправки для {participant['username']}")
            
    except Exception as e:
        print(f"Ошибка отправки уведомлений о кодах: {e}")

@app.route('/')
def index():
    """Главная страница"""
    user = session.get('user')
    
    # Если пользователь авторизован через Telegram, но не создал профиль
    if user and not user.get('profile_created'):
        return redirect(url_for('create_profile'))
    
    # Получаем турниры в зависимости от статуса пользователя
    if user and user.get('profile_created'):
        # Для авторизованных показываем все доступные турниры
        tournaments = get_tournaments_db(user_username=user['unique_username'])
    else:
        # Для неавторизованных только публичные
        tournaments = get_tournaments_db(tournament_type='public')
    
    # Получаем баланс пользователя для отображения
    user_balance = 0
    if user and user.get('profile_created'):
        user_balance = get_user_balance(int(user['id']))
    
    telegram_widget = create_telegram_login_widget(BOT_USERNAME)
    return render_template('index.html', tournaments=tournaments, bot_name=BOT_NAME, 
                         user=user, telegram_widget=telegram_widget, user_balance=user_balance)
                
@app.route('/create_tournament_page')
def create_tournament_page():
    """Страница создания турнира"""
    user = session.get('user')
    if not user or not user.get('profile_created'):
        flash('Создайте профиль для создания турниров', 'error')
        return redirect(url_for('index'))
    
    # Получаем баланс пользователя для отображения
    user_balance = get_user_balance(int(user['id']))
    
    return render_template('create_tournament.html', bot_name=BOT_NAME, user=user, user_balance=user_balance)

@app.route('/tournament/<int:tournament_id>')
def tournament_detail(tournament_id):
    """Детальная страница турнира"""
    user = session.get('user')
    
    # Получаем турнир с кодами лобби
    tournament = get_tournament_with_lobby_db(tournament_id)
    
    if not tournament:
        flash('Турнир не найден', 'error')
        return redirect(url_for('index'))
    
    # УСИЛЕННАЯ ПРОВЕРКА доступа к приватному турниру
    if tournament['tournament_type'] == 'private':
        # Создатель всегда имеет доступ
        if user and user.get('unique_username') == tournament['creator']:
            pass  # Создатель может просматривать
        else:
            # Для всех остальных - проверяем доступ в сессии
            tournament_access = session.get('tournament_access', [])
            if tournament_id not in tournament_access:
                # Нет доступа - перенаправляем на ввод пароля
                flash('Этот турнир приватный. Введите пароль для доступа.', 'error')
                return redirect(url_for('tournament_password', tournament_id=tournament_id))
    
    # Получаем список участников турнира
    tournament['participants'] = get_tournament_participants(tournament_id)
    
    # Получаем баланс пользователя для отображения
    user_balance = 0
    if user and user.get('profile_created'):
        user_balance = get_user_balance(int(user['id']))
    
    return render_template('tournament_detail.html', 
                         tournament=tournament, 
                         bot_name=BOT_NAME, 
                         user=user,
                         user_balance=user_balance)  # ← добавили баланс

@app.route('/create_profile', methods=['GET', 'POST'])
def create_profile():
    """Страница создания профиля и обработка формы"""
    
    if request.method == 'GET':
        # Отображение страницы создания профиля
        telegram_user = session.get('telegram_user')
        
        # Проверяем, не завершен ли уже процесс регистрации
        user = session.get('user')
        if user and user.get('profile_created'):
            return redirect(url_for('index'))
        
        if not telegram_user:
            flash('Сначала войдите через Telegram', 'error')
            return redirect(url_for('index'))
        
        return render_template('create_username.html', user=telegram_user, bot_name=BOT_NAME)
    
    else:  # POST
        # Обработка создания профиля
        telegram_user = session.get('telegram_user')
        if not telegram_user:
            flash('Ошибка регистрации. Войдите через Telegram заново.', 'error')
            return redirect(url_for('index'))
        
        unique_username = request.form.get('unique_username', '').strip()
        
        # Валидация никнейма
        if not re.match(r'^[a-zA-Z0-9_]{3,20}$', unique_username):
            flash('Никнейм не соответствует правилам', 'error')
            return redirect(url_for('create_profile'))
        
        # Проверка уникальности в базе данных
        if is_username_taken_db(unique_username):
            flash('Этот никнейм уже занят. Выберите другой.', 'error')
            return redirect(url_for('create_profile'))
        
        # Создаем профиль в базе данных с полными данными
        success = create_user_db(
            telegram_id=int(telegram_user['id']),
            unique_username=unique_username,
            first_name=telegram_user['first_name'],
            last_name=telegram_user.get('last_name', ''),
            photo_url=telegram_user.get('photo_url', '')
        )
        
        if success:
            # Регистрация успешна - создаем полную сессию пользователя
            session['user'] = {
                'id': telegram_user['id'],
                'first_name': telegram_user['first_name'],
                'last_name': telegram_user.get('last_name', ''),
                'photo_url': telegram_user.get('photo_url', ''),
                'profile_created': True,
                'unique_username': unique_username
            }
            
            # Удаляем временные данные регистрации
            session.pop('telegram_user', None)
            
            flash(f'🎉 Регистрация завершена! Добро пожаловать в GarantGame, {unique_username}!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Ошибка создания профиля. Попробуйте еще раз.', 'error')
            return redirect(url_for('create_profile'))

@app.route('/auth/telegram')
def telegram_auth():
    """Обработка Telegram OAuth"""
    auth_data = dict(request.args)
    
    print(f"🌐 Получены данные на сервере:")
    for key, value in auth_data.items():
        print(f"   {key}: {value}")
    
    telegram_id = auth_data.get('id')
    first_name = auth_data.get('first_name', '')
    last_name = auth_data.get('last_name', '')
    username = auth_data.get('username', '')
    photo_url = auth_data.get('photo_url', '')
    print(f"🖼️ Получена photo_url: '{photo_url}'")
    print(f"📊 Все данные: {auth_data}")
    auth_date = auth_data.get('auth_date')
    
    print(f"🖼️ photo_url после обработки: '{photo_url}'")
    
    # Базовая проверка наличия обязательных данных
    if not telegram_id or not first_name or not auth_date:
        flash('Неверные данные авторизации', 'error')
        return redirect(url_for('index'))
    
    # Проверяем, что данные не слишком старые (не более 10 минут)
    try:
        auth_timestamp = int(auth_date)
        current_time = int(time.time())
        if current_time - auth_timestamp > 600:  # 10 минут
            flash('Срок действия ссылки истек. Попробуйте войти заново.', 'error')
            return redirect(url_for('index'))
    except ValueError:
        flash('Неверный формат данных', 'error')
        return redirect(url_for('index'))
    
    try:
        telegram_id = int(telegram_id)
        
        # Проверяем, есть ли уже пользователь в базе данных
        existing_user = get_user_by_telegram_id_db(telegram_id)
        
        if existing_user:
            # СУЩЕСТВУЮЩИЙ ПОЛЬЗОВАТЕЛЬ - вход в систему
            session['user'] = {
                'id': str(telegram_id),
                'first_name': existing_user.get('first_name', first_name),
                'last_name': existing_user.get('last_name', last_name),
                'photo_url': existing_user.get('photo_url', photo_url),
                'profile_created': True,
                'unique_username': existing_user['unique_username']
            }
            flash(f'С возвращением, {existing_user["unique_username"]}! 🎮', 'success')
            return redirect(url_for('index'))
        else:
            # НОВЫЙ ПОЛЬЗОВАТЕЛЬ - начало регистрации
            session['telegram_user'] = {
                'id': str(telegram_id),
                'first_name': first_name,
                'last_name': last_name,
                'photo_url': photo_url,
            }
            flash(f'Добро пожаловать, {first_name}! Создайте уникальный игровой никнейм для завершения регистрации. 🚀', 'success')
            return redirect(url_for('create_profile'))  # ИСПРАВЛЕНО
            
    except ValueError:
        flash('Неверный ID пользователя', 'error')
        return redirect(url_for('index'))

@app.route('/logout')
def logout():
    """Выход из системы"""
    session.pop('user', None)
    session.pop('telegram_user', None)
    session.pop('tournament_access', None)  # Очищаем доступ к приватным турнирам
    flash('Вы вышли из системы', 'success')
    return redirect(url_for('index'))

@app.route('/create_tournament', methods=['POST'])
def create_tournament():
    """Создание нового турнира"""
    user = session.get('user')
    if not user or not user.get('profile_created'):
        flash('Создайте профиль для участия в турнирах', 'error')
        return redirect(url_for('index'))
    
    tournament_name = request.form.get('tournament_name')
    min_players = request.form.get('min_players', 10)
    max_players = request.form.get('max_players', 16)
    entry_fee = request.form.get('entry_fee', 0)
    tournament_type = request.form.get('tournament_type', 'public')
    tournament_password = request.form.get('tournament_password')
    start_date = request.form.get('start_date')
    start_time = request.form.get('start_time')
    prize_distribution_type = request.form.get('prize_distribution_type', 'pyramid')
    
    # Валидация
    if not tournament_name:
        flash('Введите название турнира!', 'error')
        return redirect(url_for('create_tournament_page'))
    
    # Валидация пароля для приватных турниров
    if tournament_type == 'private':
        if not tournament_password or len(tournament_password) != 6 or not tournament_password.isdigit():
            flash('Для приватного турнира требуется 6-значный пароль из цифр', 'error')
            return redirect(url_for('create_tournament_page'))
    
    try:
        min_players = int(min_players)
        max_players = int(max_players)
        entry_fee = float(entry_fee)
        
        # Проверка минимума участников в зависимости от типа турнира
        if entry_fee == 0:
            # Бесплатный турнир - минимум 40 участников
            if min_players < 40 or min_players > 100:
                flash('Для бесплатного турнира минимум участников должен быть от 40 до 100', 'error')
                return redirect(url_for('create_tournament_page'))
        else:
            # Платный турнир - минимум 10 участников
            if min_players < 10 or min_players > 100:
                flash('Для платного турнира минимум участников должен быть от 10 до 100', 'error')
                return redirect(url_for('create_tournament_page'))
            
        if max_players < 10 or max_players > 100:
            flash('Максимум участников должен быть от 10 до 100', 'error')
            return redirect(url_for('create_tournament_page'))
            
        if min_players > max_players:
            flash('Минимум участников не может быть больше максимума', 'error')
            return redirect(url_for('create_tournament_page'))
            
        if entry_fee < 0 or entry_fee > 1000:
            flash('Стоимость участия должна быть от $0 до $1000', 'error')
            return redirect(url_for('create_tournament_page'))
            
    except ValueError:
        flash('Неверные данные в форме', 'error')
        return redirect(url_for('create_tournament_page'))
    
    if not start_date or not start_time:
        flash('Укажите дату и время начала турнира', 'error')
        return redirect(url_for('create_tournament_page'))
    
    # Создаем турнир в базе данных
    tournament_id = create_tournament_db(
        name=tournament_name, 
        min_players=min_players,
        max_players=max_players, 
        creator_username=user['unique_username'],
        start_date=start_date,
        start_time=start_time,
        entry_fee=entry_fee,
        tournament_type=tournament_type,
        tournament_password=tournament_password if tournament_type == 'private' else None,
        prize_distribution_type=prize_distribution_type  # ← ДОБАВЬ ЭТУ СТРОКУ
    )
    
    if tournament_id:
        type_text = "приватный" if tournament_type == 'private' else "публичный"
        if tournament_type == 'private':
            flash(f'{type_text.capitalize()} турнир "{tournament_name}" создан! Пароль: {tournament_password}', 'success')
        else:
            flash(f'{type_text.capitalize()} турнир "{tournament_name}" создан! ID: TOUR_{tournament_id}', 'success')
    else:
        flash('Ошибка создания турнира', 'error')
    
    return redirect(url_for('index'))

@app.route('/private_tournaments')
def private_tournaments():
    """Страница только приватных турниров"""
    user = session.get('user')
    if not user or not user.get('profile_created'):
        return redirect(url_for('index'))
    
    # Получаем только приватные турниры
    all_tournaments = get_tournaments_db()
    private_tournaments = [t for t in all_tournaments if t['tournament_type'] == 'private']
    
    telegram_widget = create_telegram_login_widget(BOT_USERNAME)
    
    return render_template('private_tournaments.html', tournaments=private_tournaments, 
                         bot_name=BOT_NAME, user=user, telegram_widget=telegram_widget)

@app.route('/public_tournaments')
def public_tournaments():
    """Страница всех турниров (публичных и приватных)"""
    user = session.get('user')
    if not user or not user.get('profile_created'):
        return redirect(url_for('index'))
    
    # Получаем ВСЕ турниры (и публичные, и приватные)
    all_tournaments = get_tournaments_db()
    
    # Получаем баланс пользователя для отображения
    user_balance = get_user_balance(int(user['id']))
    
    telegram_widget = create_telegram_login_widget(BOT_USERNAME)
    
    return render_template('public_tournaments.html', tournaments=all_tournaments, 
                         bot_name=BOT_NAME, user=user, telegram_widget=telegram_widget, user_balance=user_balance)

@app.route('/join/<int:tournament_id>')
def join_tournament_web(tournament_id):
    """Присоединение к турниру через веб"""
    user = session.get('user')
    if not user or not user.get('profile_created'):
        flash('Создайте профиль для участия в турнирах', 'error')
        return redirect(url_for('index'))
    
    # Получаем турнир
    tournament = None
    tournaments = get_tournaments_db()
    for t in tournaments:
        if t['id'] == tournament_id:
            tournament = t
            break
    
    if not tournament:
        flash('Турнир не найден', 'error')
        return redirect(url_for('index'))
    
    # УСИЛЕННАЯ ПРОВЕРКА: блокируем доступ к приватному турниру без пароля
    if tournament['tournament_type'] == 'private':
        # Создатель всегда имеет доступ
        if user.get('unique_username') != tournament['creator']:
            # Проверяем, есть ли доступ в сессии
            tournament_access = session.get('tournament_access', [])
            if tournament_id not in tournament_access:
                flash('Для присоединения к приватному турниру необходимо ввести пароль', 'error')
                return redirect(url_for('tournament_password', tournament_id=tournament_id))
    
    # Проверяем, что турнир не полный
    if tournament['current_players'] >= tournament['max_players']:
        flash('Турнир уже полный', 'error')
        return redirect(url_for('tournament_detail', tournament_id=tournament_id))
    
    # Проверяем, не участвует ли уже пользователь
    participants = get_tournament_participants(tournament_id)
    for participant in participants:
        if participant['username'] == user['unique_username']:
            flash('Вы уже участвуете в этом турнире', 'error')
            return redirect(url_for('tournament_detail', tournament_id=tournament_id))
    
    # Добавляем участника
    success = add_tournament_participant(tournament_id, user['unique_username'])
    
    if success:
        if tournament['entry_fee'] > 0:
            flash(f'Вы присоединились к турниру! Оплата ${tournament["entry_fee"]} обработана.', 'success')
        else:
            flash('Вы успешно присоединились к турниру!', 'success')
    else:
        flash('Ошибка присоединения к турниру', 'error')
    
    return redirect(url_for('tournament_detail', tournament_id=tournament_id))

@app.route('/delete_tournament/<int:tournament_id>')
def delete_tournament_web(tournament_id):
    """Удаление турнира"""
    user = session.get('user')
    if not user or not user.get('profile_created'):
        flash('Вы не авторизованы', 'error')
        return redirect(url_for('index'))
    
    # Получаем турнир
    tournament = None
    tournaments = get_tournaments_db()
    for t in tournaments:
        if t['id'] == tournament_id:
            tournament = t
            break
    
    if not tournament:
        flash('Турнир не найден', 'error')
        return redirect(url_for('index'))
    
    # Проверяем права на удаление
    if tournament['creator'] != user['unique_username']:
        flash('Вы можете удалять только свои турниры', 'error')
        return redirect(url_for('index'))
    
    # Удаляем турнир
    success = delete_tournament_db(tournament_id)
    
    if success:
        flash(f'Турнир "{tournament["name"]}" удален', 'success')
    else:
        flash('Ошибка удаления турнира', 'error')
    
    return redirect(url_for('index'))

@app.route('/tournament/<int:tournament_id>/password', methods=['GET', 'POST'])
def tournament_password(tournament_id):
    """Страница ввода пароля для приватного турнира"""
    # Получаем турнир
    tournament = None
    tournaments = get_tournaments_db()
    for t in tournaments:
        if t['id'] == tournament_id:
            tournament = t
            break
    
    if not tournament:
        flash('Турнир не найден', 'error')
        return redirect(url_for('index'))
    
    if tournament['tournament_type'] != 'private':
        # Если турнир публичный, сразу переходим к деталям
        return redirect(url_for('tournament_detail', tournament_id=tournament_id))
    
    if request.method == 'GET':
        # Показываем форму ввода пароля
        return render_template('tournament_password.html', 
                             tournament=tournament, 
                             bot_name=BOT_NAME)
    
    else:  # POST
        # Проверяем пароль
        entered_password = request.form.get('password')
        
        if not entered_password:
            flash('Введите пароль', 'error')
            return render_template('tournament_password.html', 
                                 tournament=tournament, 
                                 bot_name=BOT_NAME)
        
        if entered_password == tournament['tournament_password']:
            # Пароль правильный - сохраняем доступ в сессию
            if 'tournament_access' not in session:
                session['tournament_access'] = []
            
            if tournament_id not in session['tournament_access']:
                session['tournament_access'].append(tournament_id)
            
            flash('Доступ к турниру получен!', 'success')
            return redirect(url_for('tournament_detail', tournament_id=tournament_id))
        else:
            flash('Неверный пароль. Попробуйте еще раз.', 'error')
            return render_template('tournament_password.html', 
                                 tournament=tournament, 
                                 bot_name=BOT_NAME)
                        
@app.route('/edit_tournament/<int:tournament_id>')
def edit_tournament_page(tournament_id):
    """Страница редактирования турнира"""
    user = session.get('user')
    if not user or not user.get('profile_created'):
        flash('Вы не авторизованы', 'error')
        return redirect(url_for('index'))
    
    # Получаем турнир
    tournament = None
    tournaments = get_tournaments_db()
    for t in tournaments:
        if t['id'] == tournament_id:
            tournament = t
            break
    
    if not tournament:
        flash('Турнир не найден', 'error')
        return redirect(url_for('index'))
    
    # Проверяем права на редактирование
    if tournament['creator'] != user['unique_username']:
        flash('Вы можете редактировать только свои турниры', 'error')
        return redirect(url_for('tournament_detail', tournament_id=tournament_id))
    
    # Получаем участников для отображения
    tournament['participants'] = get_tournament_participants(tournament_id)
    
    return render_template('edit_tournament.html', 
                         tournament=tournament, 
                         bot_name=BOT_NAME, 
                         user=user)

@app.route('/edit_tournament/<int:tournament_id>', methods=['POST'])
def edit_tournament(tournament_id):
    """Обработка редактирования турнира"""
    user = session.get('user')
    if not user or not user.get('profile_created'):
        flash('Вы не авторизованы', 'error')
        return redirect(url_for('index'))
    
    # Получаем турнир
    tournament = None
    tournaments = get_tournaments_db()
    for t in tournaments:
        if t['id'] == tournament_id:
            tournament = t
            break
    
    if not tournament:
        flash('Турнир не найден', 'error')
        return redirect(url_for('index'))
    
    # Проверяем права на редактирование
    if tournament['creator'] != user['unique_username']:
        flash('Вы можете редактировать только свои турниры', 'error')
        return redirect(url_for('tournament_detail', tournament_id=tournament_id))
    
    # Получаем данные из формы
    min_players = request.form.get('min_players')
    max_players = request.form.get('max_players')
    entry_fee = request.form.get('entry_fee')
    start_date = request.form.get('start_date')
    start_time = request.form.get('start_time')
    
    # Валидация
    try:
        min_players = int(min_players)
        max_players = int(max_players)
        entry_fee = float(entry_fee)
        
        # Проверяем, что новые значения не меньше текущего количества участников
        current_participants = len(get_tournament_participants(tournament_id))
        
        if min_players < current_participants:
            flash(f'Минимум участников не может быть меньше текущего количества: {current_participants}', 'error')
            return redirect(url_for('edit_tournament_page', tournament_id=tournament_id))
            
        if max_players < current_participants:
            flash(f'Максимум участников не может быть меньше текущего количества: {current_participants}', 'error')
            return redirect(url_for('edit_tournament_page', tournament_id=tournament_id))
        
        if min_players > max_players:
            flash('Минимум участников не может быть больше максимума', 'error')
            return redirect(url_for('edit_tournament_page', tournament_id=tournament_id))
            
        if entry_fee < 0 or entry_fee > 1000:
            flash('Стоимость участия должна быть от $0 до $1000', 'error')
            return redirect(url_for('edit_tournament_page', tournament_id=tournament_id))
            
    except ValueError:
        flash('Неверные данные в форме', 'error')
        return redirect(url_for('edit_tournament_page', tournament_id=tournament_id))
    
    if not start_date or not start_time:
        flash('Укажите дату и время начала турнира', 'error')
        return redirect(url_for('edit_tournament_page', tournament_id=tournament_id))
    
    # Обновляем турнир в базе данных
    success = update_tournament_db(tournament_id, min_players, max_players, entry_fee, start_date, start_time)
    
    if success:
        flash('Турнир успешно обновлен!', 'success')
        return redirect(url_for('tournament_detail', tournament_id=tournament_id))
    else:
        flash('Ошибка обновления турнира', 'error')
        return redirect(url_for('edit_tournament_page', tournament_id=tournament_id))

@app.route('/change_password/<int:tournament_id>')
def change_password_page(tournament_id):
    """Страница смены пароля турнира"""
    user = session.get('user')
    if not user or not user.get('profile_created'):
        flash('Вы не авторизованы', 'error')
        return redirect(url_for('index'))
    
    # Получаем турнир
    tournament = None
    tournaments = get_tournaments_db()
    for t in tournaments:
        if t['id'] == tournament_id:
            tournament = t
            break
    
    if not tournament:
        flash('Турнир не найден', 'error')
        return redirect(url_for('index'))
    
    # Проверяем права на изменение пароля
    if tournament['creator'] != user['unique_username']:
        flash('Вы можете изменять пароль только своих турниров', 'error')
        return redirect(url_for('tournament_detail', tournament_id=tournament_id))
    
    # Проверяем, что турнир приватный
    if tournament['tournament_type'] != 'private':
        flash('Пароль можно изменить только у приватных турниров', 'error')
        return redirect(url_for('tournament_detail', tournament_id=tournament_id))
    
    # Получаем участников для отображения
    tournament['participants'] = get_tournament_participants(tournament_id)
    
    return render_template('change_password.html', 
                         tournament=tournament, 
                         bot_name=BOT_NAME, 
                         user=user)

@app.route('/change_password/<int:tournament_id>', methods=['POST'])
def change_password(tournament_id):
    """Обработка смены пароля турнира"""
    user = session.get('user')
    if not user or not user.get('profile_created'):
        flash('Вы не авторизованы', 'error')
        return redirect(url_for('index'))
    
    # Получаем турнир
    tournament = None
    tournaments = get_tournaments_db()
    for t in tournaments:
        if t['id'] == tournament_id:
            tournament = t
            break
    
    if not tournament:
        flash('Турнир не найден', 'error')
        return redirect(url_for('index'))
    
    # Проверяем права на изменение пароля
    if tournament['creator'] != user['unique_username']:
        flash('Вы можете изменять пароль только своих турниров', 'error')
        return redirect(url_for('tournament_detail', tournament_id=tournament_id))
    
    # Проверяем, что турнир приватный
    if tournament['tournament_type'] != 'private':
        flash('Пароль можно изменить только у приватных турниров', 'error')
        return redirect(url_for('tournament_detail', tournament_id=tournament_id))
    
    # Получаем новый пароль из формы
    new_password = request.form.get('new_password')
    
    # Валидация нового пароля
    if not new_password:
        flash('Введите новый пароль', 'error')
        return redirect(url_for('change_password_page', tournament_id=tournament_id))
    
    if len(new_password) != 6 or not new_password.isdigit():
        flash('Пароль должен состоять из 6 цифр', 'error')
        return redirect(url_for('change_password_page', tournament_id=tournament_id))
    
    # Проверяем, что новый пароль отличается от старого
    if new_password == tournament['tournament_password']:
        flash('Новый пароль должен отличаться от текущего', 'error')
        return redirect(url_for('change_password_page', tournament_id=tournament_id))
    
    # Обновляем пароль в базе данных
    success = update_tournament_password_db(tournament_id, new_password)
    
    if success:
        # Сбрасываем доступы всех пользователей к этому турниру
        # (это заставит их ввести новый пароль)
        flash(f'Пароль турнира успешно изменен на: {new_password}', 'success')
        
        # Показываем уведомление о том, что участникам нужен новый пароль
        if tournament['current_players'] > 0:
            flash('⚠️ Сообщите новый пароль участникам турнира', 'warning')
        
        return redirect(url_for('tournament_detail', tournament_id=tournament_id))
    else:
        flash('Ошибка изменения пароля', 'error')
        return redirect(url_for('change_password_page', tournament_id=tournament_id))

@app.route('/lobby_codes/<int:tournament_id>')
def lobby_codes_page(tournament_id):
    """Страница управления кодами лобби"""
    user = session.get('user')
    if not user or not user.get('profile_created'):
        flash('Вы не авторизованы', 'error')
        return redirect(url_for('index'))
    
    # Получаем турнир с кодами лобби
    tournament = get_tournament_with_lobby_db(tournament_id)
    
    if not tournament:
        flash('Турнир не найден', 'error')
        return redirect(url_for('index'))
    
    # Проверяем права на управление кодами
    if tournament['creator'] != user['unique_username']:
        flash('Вы можете управлять кодами только своих турниров', 'error')
        return redirect(url_for('tournament_detail', tournament_id=tournament_id))
    
    # Получаем участников
    tournament['participants'] = get_tournament_participants(tournament_id)
    
    return render_template('lobby_codes.html', 
                         tournament=tournament, 
                         bot_name=BOT_NAME, 
                         user=user)

@app.route('/lobby_codes/<int:tournament_id>', methods=['POST'])
def lobby_codes(tournament_id):
    """Обработка кодов лобби"""
    user = session.get('user')
    if not user or not user.get('profile_created'):
        flash('Вы не авторизованы', 'error')
        return redirect(url_for('index'))
    
    # Получаем турнир
    tournament = get_tournament_with_lobby_db(tournament_id)
    
    if not tournament:
        flash('Турнир не найден', 'error')
        return redirect(url_for('index'))
    
    # Проверяем права на управление кодами
    if tournament['creator'] != user['unique_username']:
        flash('Вы можете управлять кодами только своих турниров', 'error')
        return redirect(url_for('tournament_detail', tournament_id=tournament_id))
    
    # Проверяем, нужно ли очистить коды
    if request.form.get('clear_codes'):
        success = update_lobby_codes_db(tournament_id, None, None)
        if success:
            flash('Коды лобби очищены', 'success')
        else:
            flash('Ошибка очистки кодов', 'error')
        return redirect(url_for('lobby_codes_page', tournament_id=tournament_id))
    
    # Получаем коды из формы
    lobby_id = request.form.get('lobby_id', '').strip()
    lobby_code = request.form.get('lobby_code', '').strip()
    
    # Валидация
    if not lobby_id and not lobby_code:
        flash('Введите хотя бы один код (ID или Код лобби)', 'error')
        return redirect(url_for('lobby_codes_page', tournament_id=tournament_id))
    
    if lobby_id and len(lobby_id) > 20:
        flash('ID лобби не должен превышать 20 символов', 'error')
        return redirect(url_for('lobby_codes_page', tournament_id=tournament_id))
        
    if lobby_code and len(lobby_code) > 20:
        flash('Код лобби не должен превышать 20 символов', 'error')
        return redirect(url_for('lobby_codes_page', tournament_id=tournament_id))
    
    # Обновляем коды в базе данных
    success = update_lobby_codes_db(tournament_id, lobby_id or None, lobby_code or None)

    if success:
        participants_count = len(get_tournament_participants(tournament_id))
        if participants_count > 0:
            # ОТПРАВЛЯЕМ УВЕДОМЛЕНИЯ О КОДАХ ЛОББИ
            send_lobby_codes_notifications(tournament_id, tournament['name'], lobby_id, lobby_code)
            flash(f'Коды лобби сохранены и разосланы {participants_count} участникам!', 'success')
        else:
            flash('Коды лобби сохранены (участников пока нет)', 'success')
        return redirect(url_for('tournament_detail', tournament_id=tournament_id))
    else:
        flash('Ошибка сохранения кодов', 'error')
        return redirect(url_for('lobby_codes_page', tournament_id=tournament_id))


@app.route('/balance')
def balance_page():
    """Страница баланса пользователя"""
    user = session.get('user')
    if not user or not user.get('profile_created'):
        flash('Сначала создайте профиль', 'error')
        return redirect(url_for('index'))
    
    # Получаем текущий баланс
    user_balance = get_user_balance(int(user['id']))
    
    return render_template('balance.html', 
                         user=user, 
                         user_balance=user_balance,
                         bot_name=BOT_NAME)

@app.route('/balance/topup', methods=['POST'])
def balance_topup():
    """Пополнение баланса"""
    user = session.get('user')
    if not user or not user.get('profile_created'):
        flash('Сначала создайте профиль', 'error')
        return redirect(url_for('index'))
    
    try:
        amount = float(request.form.get('amount', 0))
        
        if amount < 1 or amount > 1000:
            flash('Сумма должна быть от $1 до $1000', 'error')
            return redirect(url_for('balance_page'))
        
        # Получаем текущий баланс
        current_balance = get_user_balance(int(user['id']))
        new_balance = current_balance + amount
        
        # Обновляем баланс
        if update_user_balance(int(user['id']), new_balance):
            # Добавляем транзакцию
            add_transaction(
                int(user['id']), 
                'topup', 
                amount, 
                f'Пополнение баланса на ${amount}'
            )
            
            flash(f'💰 Баланс пополнен на ${amount:.2f}! Новый баланс: ${new_balance:.2f}', 'success')
        else:
            flash('Ошибка пополнения баланса', 'error')
            
    except ValueError:
        flash('Неверная сумма', 'error')
    
    return redirect(url_for('index'))

@app.route('/balance/history')
def balance_history():
    """История транзакций"""
    user = session.get('user')
    if not user or not user.get('profile_created'):
        flash('Сначала создайте профиль', 'error')
        return redirect(url_for('index'))
    
    # Пока что просто перенаправляем обратно
    flash('История транзакций будет добавлена позже', 'warning')
    return redirect(url_for('balance_page'))

@app.route('/join_with_balance/<int:tournament_id>')
def join_tournament_with_balance(tournament_id):
    """Присоединение к турниру с оплатой из баланса"""
    user = session.get('user')
    if not user or not user.get('profile_created'):
        flash('Создайте профиль для участия в турнирах', 'error')
        return redirect(url_for('index'))
    
    # Получаем турнир
    tournament = None
    tournaments = get_tournaments_db()
    for t in tournaments:
        if t['id'] == tournament_id:
            tournament = t
            break
    
    if not tournament:
        flash('Турнир не найден', 'error')
        return redirect(url_for('index'))
    
    # Проверяем, что турнир не полный
    if tournament['current_players'] >= tournament['max_players']:
        flash('Турнир уже полный', 'error')
        return redirect(url_for('tournament_detail', tournament_id=tournament_id))
    
    # Проверяем, не участвует ли уже пользователь
    participants = get_tournament_participants(tournament_id)
    for participant in participants:
        if participant['username'] == user['unique_username']:
            flash('Вы уже участвуете в этом турнире', 'error')
            return redirect(url_for('tournament_detail', tournament_id=tournament_id))
    
    # Бесплатный турнир
    if tournament['entry_fee'] == 0:
        success = add_tournament_participant(tournament_id, user['unique_username'])
        if success:
            flash('Вы успешно присоединились к бесплатному турниру!', 'success')
        else:
            flash('Ошибка присоединения к турниру', 'error')
        return redirect(url_for('tournament_detail', tournament_id=tournament_id))
    
    # Платный турнир - списываем с баланса
    success, message = process_tournament_payment_from_balance(
        int(user['id']), 
        tournament_id, 
        user['unique_username'], 
        tournament['entry_fee']
    )
    
    if success:
        flash(f'✅ {message}', 'success')
    else:
        flash(f'❌ {message}', 'error')
        # Если недостаточно средств, предлагаем пополнить
        if "Недостаточно средств" in message:
            flash('💡 Пополните баланс для участия в турнире', 'warning')
    
    return redirect(url_for('tournament_detail', tournament_id=tournament_id))



if __name__ == '__main__':
    print(f"🌐 Веб-интерфейс {BOT_NAME} запущен!")
    print("📱 Откройте: http://localhost:8000")
    app.run(debug=True, port=8000)