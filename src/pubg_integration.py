import requests
import json
import sys
import os
from datetime import datetime

# Добавляем путь к config
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from config.settings import PUBG_API_KEY

class PUBGMatchTracker:
    def __init__(self):
        self.api_key = PUBG_API_KEY
        self.base_url = "https://api.pubg.com"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/vnd.api+json"
        }
    
    def get_match_results(self, match_id):
        """Получить результаты матча для турнира"""
        print(f"🎮 Получаем результаты матча {match_id}...")
        
        try:
            url = f"{self.base_url}/shards/tournament/matches/{match_id}"
            response = requests.get(url, headers=self.headers)
            
            if response.status_code != 200:
                return {"error": f"API error: {response.status_code}"}
            
            data = response.json()
            
            # Получаем участников
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
                    "survival_time": self._format_time(stats.get('timeSurvived', 0)),
                    "headshots": stats.get('headshotKills', 0),
                    "assists": stats.get('assists', 0),
                    "walk_distance": round(stats.get('walkDistance', 0), 2)
                }
                results.append(result)
            
            # Сортируем по месту
            results.sort(key=lambda x: x['placement'])
            
            return {
                "success": True,
                "match_id": match_id,
                "total_players": len(results),
                "results": results
            }
            
        except Exception as e:
            return {"error": f"Exception: {str(e)}"}
    
    def _format_time(self, seconds):
        """Форматировать время в MM:SS"""
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes:02d}:{secs:02d}"