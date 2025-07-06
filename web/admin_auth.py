import sys
import os
from functools import wraps
from flask import session, redirect, url_for, flash

# Добавляем путь к config
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from config.settings import ADMIN_TELEGRAM_IDS, ADMIN_USERNAMES

def is_admin(user):
    """Проверить, является ли пользователь админом"""
    if not user:
        return False
    
    # Проверка по Telegram ID
    try:
        telegram_id = int(user.get('id', 0))
        if telegram_id in ADMIN_TELEGRAM_IDS:
            return True
    except:
        pass
    
    # Проверка по unique_username с сайта
    site_username = user.get('unique_username', '')
    if site_username in ADMIN_USERNAMES:
        return True
    
    return False

def admin_required(f):
    """Декоратор для проверки прав админа"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = session.get('user')
        
        if not user or not user.get('profile_created'):
            flash('Войдите в систему', 'error')
            return redirect(url_for('index'))
        
        if not is_admin(user):
            flash('Доступ запрещен. Нужны права администратора.', 'error')
            return redirect(url_for('index'))
        
        return f(*args, **kwargs)
    return decorated_function