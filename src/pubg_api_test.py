import requests
import json

def check_pubg_apis():
    """Проверка доступных PUBG API"""
    print("🔍 Проверяем реальные API для PUBG Mobile...\n")
    
    # 1. Официальный PUBG API (проверим поддержку Mobile)
    print("1. 🏢 Официальный PUBG API:")
    try:
        response = requests.get("https://api.pubg.com/status", timeout=5)
        print(f"   Статус: {response.status_code}")
        if response.status_code == 200:
            print("   ✅ API доступен (но нужен ключ)")
        else:
            print("   ❌ API недоступен")
    except:
        print("   ❌ Не удалось подключиться")
    
    # 2. PUBG Tracker API
    print("\n2. 📊 PUBG Tracker API:")
    try:
        # Тестовый запрос без ключа
        response = requests.get("https://api.tracker.gg/api/v2/pubg-mobile/", timeout=5)
        print(f"   Статус: {response.status_code}")
        if response.status_code == 401:
            print("   🔑 Требует API ключ, но API работает")
        elif response.status_code == 200:
            print("   ✅ API доступен")
    except:
        print("   ❌ Не удалось подключиться")
    
    # 3. Проверим другие варианты
    print("\n3. 🔎 Другие варианты:")
    
    # Список игроков для тестирования (без реальных запросов)
    test_endpoints = [
        "https://chicken-dinner.com/api/",
        "https://pubgop.gg/api/",
        "https://www.op.gg/api/pubgm/"
    ]
    
    for endpoint in test_endpoints:
        try:
            response = requests.head(endpoint, timeout=3)
            print(f"   📋 {endpoint}: статус {response.status_code}")
        except:
            print(f"   ❌ {endpoint}: недоступен")

def test_pubg_mobile_data_format():
    """Тестируем какие данные нужны для турнира"""
    print("\n" + "="*50)
    print("📋 КАКИЕ ДАННЫЕ НУЖНЫ ДЛЯ ТУРНИРА:")
    print()
    
    # Структура данных которые мы хотим получить
    tournament_data = {
        "tournament_id": "TOUR_123",
        "lobby_id": "ROOM123456", 
        "lobby_code": "PASS789",
        "match_results": [
            {
                "player_name": "PlayerName",
                "placement": 1,
                "kills": 8,
                "damage": 1250.5,
                "survival_time": "25:30"
            }
        ]
    }
    
    print("Нужные данные:")
    print("✅ ID лобби (у нас есть)")
    print("✅ Код лобби (у нас есть)")
    print("❓ Результаты матча:")
    print("   - Место каждого игрока (1-100)")
    print("   - Количество убийств")
    print("   - Нанесенный урон")
    print("   - Время выживания")
    print()
    print("📝 Пример структуры данных:")
    print(json.dumps(tournament_data, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    check_pubg_apis()
    test_pubg_mobile_data_format()