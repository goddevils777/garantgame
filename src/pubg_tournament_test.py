def find_tournament_match_real(self, tournament_participants, lobby_start_time):
    """РЕАЛЬНЫЙ поиск матча турнира"""
    print(f"🔍 РЕАЛЬНЫЙ поиск матча турнира")
    print(f"👥 Участников: {len(tournament_participants)}")
    print(f"⏰ Время старта: {lobby_start_time}")
    
    # Получаем PUBG никнеймы участников
    pubg_nicks = [p['pubg_nickname'] for p in tournament_participants if p['pubg_nickname']]
    
    if len(pubg_nicks) < 2:
        return {"error": "Нужно минимум 2 участника с PUBG никнеймами"}
    
    print(f"🎮 PUBG ники: {pubg_nicks}")
    
    # Шаг 1: Берем первого участника
    first_player = pubg_nicks[0]
    print(f"🔍 Ищем матчи игрока: {first_player}")
    
    # Шаг 2: Получаем его недавние матчи
    player_matches = self.get_player_recent_matches(first_player)
    
    if "error" in player_matches:
        return {"error": f"Игрок {first_player} не найден: {player_matches['error']}"}
    
    print(f"📊 Найдено {len(player_matches['matches'])} недавних матчей")
    
    # Шаг 3: Проверяем каждый матч
    for i, match_id in enumerate(player_matches['matches']):
        print(f"\n🔍 Проверяем матч {i+1}/{len(player_matches['matches'])}: {match_id}")
        
        # Получаем базовую информацию о матче
        match_info = self.get_match_basic_info(match_id)
        
        if "error" in match_info:
            print(f"❌ Ошибка получения info: {match_info['error']}")
            continue
        
        # Проверка 1: Это кастомный матч?
        if not match_info.get('isCustomMatch', False):
            print(f"❌ Не кастомный матч")
            continue
        
        print(f"✅ Кастомный матч!")
        
        # Проверка 2: Время матча после старта турнира?
        match_time = match_info.get('createdAt', '')
        if not self._is_after_time(match_time, lobby_start_time):
            print(f"❌ Матч до времени турнира ({match_time})")
            continue
            
        print(f"✅ Матч после времени турнира!")
        
        # Проверка 3: Получаем участников матча
        match_results = self.get_full_match_results(match_id)
        
        if "error" in match_results:
            print(f"❌ Ошибка получения результатов: {match_results['error']}")
            continue
        
        # Проверка 4: Сколько наших участников в матче?
        match_players = [p['player_name'] for p in match_results['results']]
        our_players = [nick for nick in pubg_nicks if nick in match_players]
        
        our_percentage = len(our_players) / len(pubg_nicks) * 100
        
        print(f"👥 Наших игроков: {len(our_players)}/{len(pubg_nicks)} ({our_percentage:.1f}%)")
        print(f"🎯 Найденные: {our_players}")
        
        # Проверка 5: >= 80% наших участников?
        if our_percentage >= 80:
            print(f"🎉 НАЙДЕН МАТЧ ТУРНИРА!")
            
            # Фильтруем только наших участников
            filtered_results = []
            for player in match_results['results']:
                if player['player_name'] in pubg_nicks:
                    # Связываем с username на сайте
                    for participant in tournament_participants:
                        if participant['pubg_nickname'] == player['player_name']:
                            player['site_username'] = participant['username']
                            break
                    filtered_results.append(player)
            
            return {
                "success": True,
                "method": "real_search",
                "match_id": match_id,
                "our_players_found": our_players,
                "match_info": match_info,
                "results": filtered_results
            }
        else:
            print(f"❌ Недостаточно наших игроков ({our_percentage:.1f}% < 80%)")
    
    return {"error": f"Матч турнира не найден среди {len(player_matches['matches'])} недавних игр"}

def get_match_basic_info(self, match_id):
    """Получить базовую информацию о матче"""
    try:
        url = f"{self.base_url}/shards/tournament/matches/{match_id}"
        response = requests.get(url, headers=self.headers)
        
        if response.status_code != 200:
            return {"error": f"HTTP {response.status_code}"}
        
        data = response.json()
        attrs = data.get('data', {}).get('attributes', {})
        
        return {
            "success": True,
            "createdAt": attrs.get('createdAt'),
            "isCustomMatch": attrs.get('isCustomMatch', False),
            "mapName": attrs.get('mapName'),
            "gameMode": attrs.get('gameMode'),
            "duration": attrs.get('duration')
        }
        
    except Exception as e:
        return {"error": f"Exception: {str(e)}"}

def _is_after_time(self, match_time, lobby_start_time):
    """Проверить что матч после времени лобби"""
    try:
        from datetime import datetime
        
        # Парсим время матча (ISO формат)
        match_dt = datetime.fromisoformat(match_time.replace('Z', '+00:00'))
        
        # Парсим время лобби
        if isinstance(lobby_start_time, str):
            lobby_dt = datetime.fromisoformat(lobby_start_time)
        else:
            lobby_dt = lobby_start_time
            
        result = match_dt > lobby_dt
        print(f"⏰ Сравнение времени: матч {match_dt} > лобби {lobby_dt} = {result}")
        return result
        
    except Exception as e:
        print(f"⚠️ Ошибка сравнения времени: {e}")
        return True  # Если не можем сравнить - считаем подходящим