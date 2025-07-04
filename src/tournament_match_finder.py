import requests
import json
import sys
import os
from datetime import datetime, timedelta

# Добавляем путь к config
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from config.settings import PUBG_API_KEY

class TournamentMatchFinder:
    def __init__(self):
        self.api_key = PUBG_API_KEY
        self.base_url = "https://api.pubg.com"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/vnd.api+json"
        }
    
    def find_tournament_match_real(self, tournament_participants, lobby_start_time):
        """РЕАЛЬНЫЙ поиск матча турнира"""
        print(f"🔍 РЕАЛЬНЫЙ поиск матча турнира")
        return {"error": "Функция пока в разработке - используйте ручной поиск"}
    
    def test_with_known_match(self):
        """Тест с известным Match ID - работающая функция"""
        print(f"🧪 ТЕСТ с известным Match ID")
        
        known_match_id = "d79dbc5d-c215-4148-a164-a38977b11bae"
        
        # Получаем результаты известного матча
        match_results = self.get_full_match_results(known_match_id)
        
        if "error" in match_results:
            print(f"❌ Ошибка: {match_results['error']}")
            return {"error": match_results['error']}
        
        print(f"✅ Матч загружен!")
        print(f"👥 Всего игроков: {len(match_results['results'])}")
        
        return {
            "success": True,
            "match_id": known_match_id,
            "total_players": len(match_results['results']),
            "results": match_results['results']
        }
    
    def get_full_match_results(self, match_id):
        """Получить полные результаты матча"""
        try:
            url = f"{self.base_url}/shards/tournament/matches/{match_id}"
            response = requests.get(url, headers=self.headers)
            
            if response.status_code != 200:
                return {"error": f"HTTP {response.status_code}"}
            
            data = response.json()
            included = data.get('included', [])
            participants = [item for item in included if item.get('type') == 'participant']
            
            results = []
            for participant in participants:
                stats = participant.get('attributes', {}).get('stats', {})
                
                result = {
                    "player_name": stats.get('name', 'Unknown'),
                    "placement": stats.get('winPlace', 0),
                    "kills": stats.get('kills', 0),
                    "damage": round(stats.get('damageDealt', 0), 2),
                    "survival_time": self._format_time(stats.get('timeSurvived', 0))
                }
                results.append(result)
            
            # Сортируем по месту
            results.sort(key=lambda x: x['placement'])
            
            return {
                "success": True,
                "results": results
            }
            
        except Exception as e:
            return {"error": f"Exception: {str(e)}"
    
    def _format_time(self, seconds):
        """Форматировать время в MM:SS"""
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes:02d}:{secs:02d}"

    def test_real_player_search(self, player_name):
        """Тест поиска реального игрока"""
        print(f"🔍 ТЕСТ: Ищем реального игрока {player_name}")
        
        player_matches = self.get_player_recent_matches(player_name)
        
        if "error" in player_matches:
            print(f"❌ Игрок не найден: {player_matches['error']}")
            return {"error": player_matches['error']}
        
        print(f"✅ Найдено {len(player_matches['matches'])} матчей для {player_name}")
        print(f"📊 Платформа: {player_matches['platform']}")
        
        if len(player_matches['matches']) > 0:
            first_match = player_matches['matches'][0]
            print(f"🎮 Первый матч: {first_match}")
            
            # Проверим этот матч
            match_info = self.get_match_basic_info(first_match)
            if "error" not in match_info:
                print(f"✅ Инфо о матче получена:")
                print(f"   🗺️ Карта: {match_info.get('mapName', 'N/A')}")
                print(f"   🎮 Режим: {match_info.get('gameMode', 'N/A')}")
                print(f"   🔧 Кастомный: {match_info.get('isCustomMatch', False)}")
                print(f"   ⏰ Время: {match_info.get('createdAt', 'N/A')}")
        
        return {"success": True, "matches_found": len(player_matches['matches'])}

if __name__ == "__main__":
    finder = TournamentMatchFinder()
    
    # Тест поиска реального игрока
    finder.test_real_player_search("82_SINGAM")

        