import requests
import json
import sys
import os

# Добавляем путь к config
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from config.settings import PUBG_API_KEY

class PUBGAPIClient:
    def __init__(self):
        self.api_key = PUBG_API_KEY
        self.base_url = "https://api.pubg.com"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/vnd.api+json"
        }
    
    def test_connection(self):
        """Тест подключения к API"""
        print("🔑 Тестируем API ключ...")
        try:
            response = requests.get(f"{self.base_url}/status", headers=self.headers)
            print(f"📊 Статус ответа: {response.status_code}")
            
            if response.status_code == 200:
                print("✅ API ключ работает отлично!")
                print("📈 Лимит: 10 запросов/минуту = 14,400/день")
                print("💡 Этого хватит на тысячи турниров!")
                return True
            else:
                print(f"❌ Ошибка: {response.text}")
                return False
        except Exception as e:
            print(f"❌ Ошибка подключения: {e}")
            return False

    def explore_api_endpoints(self):
        """Изучаем что доступно в PUBG API"""
        print("\n🔍 Изучаем доступные платформы и регионы...")
        
        platforms = ['steam', 'xbox', 'psn', 'kakao', 'stadia', 'tournament']
        
        for platform in platforms:
            try:
                url = f"{self.base_url}/shards/{platform}/players"
                response = requests.get(url, headers=self.headers, params={'filter[playerNames]': 'test'})
                print(f"📱 Платформа {platform}: статус {response.status_code}")
                
                if response.status_code == 404:
                    print(f"   ❌ {platform} не поддерживается")
                elif response.status_code == 400:
                    print(f"   ✅ {platform} доступна (плохой запрос - это нормально)")
                elif response.status_code == 200:
                    print(f"   ✅ {platform} полностью доступна")
                    
            except Exception as e:
                print(f"   ❌ Ошибка проверки {platform}: {e}")

    def check_tournament_platform(self):
        """Проверяем турнирную платформу"""
        print("\n🏆 Проверяем турнирную платформу...")
        
        try:
            url = f"{self.base_url}/tournaments"
            response = requests.get(url, headers=self.headers)
            print(f"📊 Турниры: статус {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print("✅ Турнирные данные доступны!")
                print(f"📋 Структура: {list(data.keys())}")
            elif response.status_code == 404:
                print("❌ Турнирные данные недоступны")
            else:
                print(f"⚠️ Неожиданный ответ: {response.text[:200]}")
                
        except Exception as e:
            print(f"❌ Ошибка: {e}")

    def explore_tournament_data(self):
            """Изучаем структуру турнирных данных"""
            print("\n📋 Изучаем турнирные данные подробно...")
            
            try:
                url = f"{self.base_url}/tournaments"
                response = requests.get(url, headers=self.headers)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    print(f"📊 Найдено турниров: {len(data.get('data', []))}")
                    
                    if data.get('data'):
                        # Смотрим первый турнир
                        first_tournament = data['data'][0]
                        print(f"🏆 Первый турнир:")
                        print(f"   ID: {first_tournament.get('id')}")
                        print(f"   Тип: {first_tournament.get('type')}")
                        
                        # Смотрим атрибуты
                        attrs = first_tournament.get('attributes', {})
                        print(f"   📋 Атрибуты: {list(attrs.keys())}")
                        
                        # Ищем игру
                        if 'gameMode' in attrs:
                            print(f"   🎮 Режим игры: {attrs['gameMode']}")
                        
                        # Смотрим связи
                        relationships = first_tournament.get('relationships', {})
                        print(f"   🔗 Связи: {list(relationships.keys())}")
                        
                    else:
                        print("📭 Активных турниров не найдено")
                        
            except Exception as e:
                print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    client = PUBGAPIClient()
    if client.test_connection():
        client.explore_api_endpoints()
        client.check_tournament_platform()
        client.explore_tournament_data()