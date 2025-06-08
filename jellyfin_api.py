import json
import requests


class JellyfinClient:
    def __init__(self, base_url: str, api_key: str, username: str):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.username = username
        self.headers = {
            'X-Emby-Token': self.api_key,
            'Accept': 'application/json'
        }
        self.user_id = self._get_user_id_from_username()

    def _get_user_id_from_username(self):
        url = f"{self.base_url}/Users"
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            users = response.json()
            for user in users:
                if user.get("Name") == self.username:
                    return user.get("Id")
            print(f"Utilisateur '{self.username}' non trouvé.")
            return None
        except Exception as e:
            print(f"Erreur lors de la récupération des utilisateurs : {e}")
            return None

    def _get_first_episode_languages(self, series_id):
        """
        Récupère les langues audio du premier épisode d'une série.
        """
        url = f"{self.base_url}/Shows/{series_id}/Episodes"
        params = {
            'UserId': self.user_id,
            'Limit': 1,
            'Fields': 'MediaStreams'
        }

        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            episodes = response.json().get('Items', [])
            if not episodes:
                return []

            media_streams = episodes[0].get('MediaStreams', [])
            return list({
                stream.get('Language') for stream in media_streams
                if stream.get('Type') == 'Audio' and stream.get('Language')
            })

        except Exception:
            return []

    def get_shows(self, limit=1000):
        if not self.user_id:
            print("Impossible de continuer sans UserId.")
            return []

        url = f"{self.base_url}/Items"
        params = {
            'IncludeItemTypes': 'Movie,Series',
            'Recursive': 'true',
            'Fields': 'MediaStreams,UserData,Overview',
            'Limit': limit,
            'UserId': self.user_id
        }

        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            items = response.json().get('Items', [])
            result = []

            for item in items:
                media_type = item.get('Type')
                if media_type not in ['Movie', 'Series']:
                    continue

                type_label = 'film' if media_type == 'Movie' else 'serie'

                # Langues audio
                if media_type == 'Movie':
                    media_streams = item.get('MediaStreams', [])
                    audio_languages = list({
                        stream.get('Language') for stream in media_streams
                        if stream.get('Type') == 'Audio' and stream.get('Language')
                    })
                else:
                    # Pour les séries, chercher un épisode pour récupérer les langues
                    audio_languages = self._get_first_episode_languages(item.get('Id'))

                user_data = item.get('UserData', {})
                is_played = user_data.get('Played', False)
                play_percentage = user_data.get('PlayPercentage', 0)
                seen = is_played or (play_percentage and play_percentage >= 90)

                result.append({
                    'title': item.get('Name'),
                    'type': type_label,
                    'languages': audio_languages,
                    'seen': bool(seen),
                    'description': item.get('Overview', '')[:100]
                })

            return result

        except requests.exceptions.RequestException as e:
            print(f"Erreur lors de la requête Jellyfin : {e}")
            return []

    def save_to_json(self, data, filename="shows.json"):
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False)
            print(f"Fichier JSON sauvegardé : {filename}")
        except Exception as e:
            print(f"Erreur lors de la sauvegarde : {e}")
