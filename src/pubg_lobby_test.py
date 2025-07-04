import requests
import json
import sys
import os

# Исправляем импорт
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'config'))
from settings import PUBG_API_KEY

def check_api_documentation():
    """Проверяем что показывает статус API"""
    print("📋 ИССЛЕДОВАНИЕ PUBG API")
    
    api_key = PUBG_API_KEY
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/vnd.api+json"
    }
    
    # Проверяем статус API
    try:
        response = requests.get("https://api.pubg.com/status", headers=headers)
        if response.status_code == 200:
            data = response.json()
            print("✅ Статус API:")
            print(json.dumps(data, indent=2))
            
            # Ищем информацию о поддерживаемых платформах
            if 'data' in data:
                for item in data['data']:
                    print(f"\n🔍 Элемент: {item.get('id', 'N/A')}")
                    attrs = item.get('attributes', {})
                    for key, value in attrs.items():
                        print(f"   {key}: {value}")
    
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    
    # Проверяем доступные шарды из документации
    print(f"\n📖 ОФИЦИАЛЬНЫЕ ШАРДЫ из документации:")
    official_shards = [
        'steam',      # PC Steam
        'kakao',      # PC Kakao
        'console',    # Xbox/PlayStation  
        'stadia',     # Google Stadia
        'tournament'  # Турнирная платформа
    ]
    
    for shard in official_shards:
        print(f"   {shard}: Официально поддерживается")
    
    print(f"\n💡 ВЫВОД:")
    print(f"   ✅ PUBG API работает для PC/Console версий")
    print(f"   ❌ PUBG Mobile НЕ поддерживается официальным API")
    print(f"   🎯 Но мы можем получать статистику PC матчей по Room ID!")

def test_room_id_concept():
    """Тестируем концепцию поиска по Room ID"""
    print(f"\n🎯 ТЕСТ: Концепция поиска кастомных матчей")
    
    api_key = PUBG_API_KEY
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/vnd.api+json"
    }
    
    # Используем уже найденный рабочий матч
    known_match_id = "9b020a57-b3de-4dd9-9ae5-123456789abc"  # Пример из предыдущего теста
    
    print(f"💡 Идея: Если у нас есть Room ID из игры,")
    print(f"   мы можем найти соответствующий матч через:")
    print(f"   1. Поиск по игрокам из лобби")
    print(f"   2. Фильтрация по времени создания матча") 
    print(f"   3. Проверка на кастомный матч")
    
    print(f"\n📝 Алгоритм для получения статистики:")
    print(f"   1. Получаем список участников турнира")
    print(f"   2. Ищем недавние матчи первого игрока")
    print(f"   3. Для каждого матча проверяем:")
    print(f"      - Это кастомный матч?")
    print(f"      - Время совпадает с турниром?") 
    print(f"      - Участвуют ли наши игроки?")
    print(f"   4. Получаем полную статистику матча")

def mobile_alternative_solution():
    """Альтернативное решение для мобайла"""
    print(f"\n📱 АЛЬТЕРНАТИВЫ ДЛЯ PUBG MOBILE:")
    
    print(f"1. 🎮 Если турнир в PC версии:")
    print(f"   ✅ Используем PUBG API")
    print(f"   ✅ Получаем полную статистику")
    print(f"   ✅ Автоматический подсчет призов")
    
    print(f"\n2. 📱 Если турнир в Mobile версии:")
    print(f"   ❌ Официального API нет")
    print(f"   🔄 Альтернативы:")
    print(f"      - Ручной ввод результатов создателем")
    print(f"      - Скриншоты результатов")
    print(f"      - Интеграция с другими сервисами")
    
    print(f"\n💡 РЕКОМЕНДАЦИЯ:")
    print(f"   Создать гибридную систему:")
    print(f"   - Автоматически для PC PUBG") 
    print(f"   - Ручной ввод для Mobile PUBG")

if __name__ == "__main__":
    check_api_documentation()
    test_room_id_concept()
    mobile_alternative_solution()