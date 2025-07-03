import hashlib
import hmac
import time
from urllib.parse import parse_qs
from config.settings import BOT_TOKEN

def verify_telegram_auth(auth_data):
    """Проверка подлинности данных от Telegram"""
    check_hash = auth_data.pop('hash', '')
    data_check_string = '\n'.join([f"{k}={v}" for k, v in sorted(auth_data.items())])
    
    secret_key = hashlib.sha256(BOT_TOKEN.encode()).digest()
    calculated_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
    
    # Проверяем hash и время (данные не старше 1 дня)
    if calculated_hash == check_hash and (time.time() - int(auth_data.get('auth_date', 0))) < 86400:
        return True
    return False

def create_telegram_login_widget(bot_username):
    """Создает кнопку для авторизации через Telegram бота"""
    return f'''
    <div style="text-align: center;">
        <a href="https://t.me/{bot_username}?start=auth" 
           style="display: inline-block; background: linear-gradient(135deg, #0088cc 0%, #006699 100%); 
                  color: white; padding: 15px 30px; border-radius: 25px; text-decoration: none; 
                  font-weight: bold; font-size: 16px; box-shadow: 0 4px 15px rgba(0,136,204,0.3);
                  transition: all 0.3s;"
           onmouseover="this.style.transform='translateY(-2px)'"
           onmouseout="this.style.transform='translateY(0)'"
           target="_blank">
            📱 Войти через Telegram
        </a>
        <p style="margin-top: 15px; font-size: 14px; color: #666; max-width: 300px; margin-left: auto; margin-right: auto;">
            Нажмите кнопку выше, чтобы открыть Telegram и подтвердить вход в систему
        </p>
        <div style="margin-top: 15px; padding: 10px; background: #e3f2fd; border-radius: 10px; font-size: 13px; color: #1976d2;">
            💡 <strong>Как это работает:</strong><br>
            1. Нажмите кнопку "Войти через Telegram"<br>
            2. Откроется ваш Telegram<br>
            3. Нажмите "START" в боте<br>
            4. Бот даст вам ссылку для возврата на сайт
        </div>
    </div>
    '''
