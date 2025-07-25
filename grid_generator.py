import json
import os
import pprint
import random
from collections import defaultdict

import requests
from dotenv import load_dotenv

from data_types import Show, CategoryCriteria, Criteria, SlotFormat, ChannelBlock, Channel
from utils import deserialize_enum_keys

load_dotenv()


class ShowSelector:

    def __init__(self, channel: Channel, show_list: list[Show], other_channels: list[Channel] = None):
        self.channel = channel
        self.show_list = show_list
        self.other_channels = other_channels

    def generate_schedules(self):
        for block in self.channel['blocks']:
            matching_shows = self.get_matching_shows(self.show_list, block['criteria'])
            block['shows'] = matching_shows
        self.curate_channel(self.channel)

    def get_matching_shows(self, show_list: list[Show], criteria: list[Criteria]):
        matching_shows = []
        for show in show_list:
            matches = []
            for crit in criteria:
                matches.append(self.check_criteria(show, crit))
            if all(matches):
                matching_shows.append(show)
        return matching_shows

    @staticmethod
    def curate_channel(channel: Channel):
        for block in channel['blocks']:
            items = block['shows']
            random.shuffle(items)
            block['shows'] = items[:10]

    @staticmethod
    def check_criteria(show: Show, criteria: Criteria) -> bool:
        values = criteria['values']
        category = criteria['category']
        show_properties = show.get('properties', {})
        if len(values) > 0:
            props = set(show_properties.get(category, []))
            if criteria['category'] == CategoryCriteria.DURATION:
                if all([i is not None for i in props]):
                    if "totoro" in show['name'].lower():
                        print(min(values) < min(props) and max(props) < max(values), props, values)
                    return min(values) < min(props) and max(props) < max(values)
            else:
                return any(props.intersection(set(values)))
        return False


class ChannelMaker:

    def __init__(self, available_properties: dict[CategoryCriteria, list[str | int | float]]):
        self.available_properties = available_properties
        self.channel: Channel = dict()
        self.channel_begin_at = 6
        self.channel_end_at = 4
        self.available_slot_formats: list[SlotFormat] = [
            {"show_min_duration": 22, "show_max_duration": 26, "slot_duration": 30},  # Sitcoms, courts magazines
            {"show_min_duration": 45, "show_max_duration": 52, "slot_duration": 60},  # Séries, documentaires
            {"show_min_duration": 70, "show_max_duration": 80, "slot_duration": 90},  # Téléfilms, unitaires
            {"show_min_duration": 95, "show_max_duration": 110, "slot_duration": 120},  # Films du soir
            {"show_min_duration": 12, "show_max_duration": 13, "slot_duration": 15},  # Pastilles courtes
        ]

        self.slot_count_options = [1, 2, 3]

    def make_channel_frame(self):
        self.set_slot_config()
        self.set_properties()
        self.set_blocks()

    def set_properties(self):
        result = {}
        for key in self.available_properties:
            options = self.available_properties[key]
            option_kept = self.multiple_random_selection(options, 10)
            result[key] = option_kept
        self.channel['available_properties'] = result

    def set_slot_config(self):
        selected_slot_formats = self.multiple_random_selection(self.available_slot_formats, 2)
        selected_slot_counts = self.multiple_random_selection(self.slot_count_options, 2)
        self.channel["available_slot_count"] = selected_slot_counts
        self.channel["available_slow_format"] = selected_slot_formats
        self.channel['begin'] = self.channel_begin_at
        self.channel["end"] = self.channel_end_at

    def set_blocks(self):
        begin = self.channel['begin']
        blocks: list[ChannelBlock] = []
        force_minimum = False
        retry = 0
        while True:
            block = self.generate_block(begin, force_minimum)
            if block:
                begin = block['end']
                blocks.append(block)
                retry = 0
            else:
                force_minimum = True
                retry += 1
            if retry > 1:
                break
        self.channel['blocks'] = blocks

    def generate_block(self, begin: int, force_minimum=False) -> ChannelBlock | None:
        block: ChannelBlock = dict()
        block['begin'] = begin

        selected_slow_format: SlotFormat = random.choice(self.channel['available_slow_format']) if not force_minimum \
            else min(self.channel['available_slow_format'], key=lambda s: s["slot_duration"])

        selected_slot_count = random.choice(self.channel['available_slot_count']) if not force_minimum else min(
            self.channel['available_slot_count'])

        block_duration = self.minute_to_float_hour(selected_slow_format["slot_duration"] * selected_slot_count)
        end_date = block['begin'] + block_duration
        normalized_end_date = self.normalize_hour_to_day(end_date)

        if end_date != normalized_end_date and normalized_end_date > self.channel['end']:
            return None
        block['end'] = end_date  # normalized_end_date
        block['slot_count'] = selected_slot_count
        block['slow_format'] = selected_slow_format
        block['criteria'] = self.select_block_criteria(selected_slow_format)
        return block

    def select_block_criteria(self, slot_duration: SlotFormat) -> list[Criteria]:
        result = []
        available_properties = self.channel['available_properties']
        for prop in available_properties:
            criteria: Criteria = dict()
            if prop == CategoryCriteria.DURATION:
                criteria['category'] = CategoryCriteria.DURATION
                criteria["values"] = [slot_duration['show_min_duration'], slot_duration['show_max_duration']]
            else:
                values = available_properties[prop]
                selected = self.multiple_random_selection(values, 3)
                criteria['category'] = prop
                criteria["values"] = selected

            result.append(criteria)
        return result

    @staticmethod
    def multiple_random_selection(options: list[any], maximum_option_count):
        option_count = len(options)
        option_count = option_count if option_count < maximum_option_count else maximum_option_count
        option_kept_count = random.randint(1, option_count)
        random.shuffle(options)
        option_kept = options[:option_kept_count]
        return option_kept

    @staticmethod
    def minute_to_float_hour(duration: int | float) -> float:
        return duration / 60

    @staticmethod
    def normalize_hour_to_day(hour: float) -> float:
        return hour if hour < 24 else hour - 24


class JellyfinShowRetriever:

    def __init__(self, base_url: str, api_key: str, username: str):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.username = username
        self.headers = {
            'X-Emby-Token': self.api_key,
            'Accept': 'application/json'
        }
        self.user_id = self.get_user_id_from_username()

        self.data_dir = "data"
        self.show_file_path = os.path.join(self.data_dir, "shows.json")

    def get_shows(self, limit=100) -> list[Show]:
        if os.path.exists(self.show_file_path):
            return self.load_shows()
        show_list = self._get_shows(limit)
        self.save_shows(show_list)
        return show_list

    def _get_shows(self, limit=100) -> list[Show]:
        url = f"{self.base_url}/Items"
        params = {
            'IncludeItemTypes': 'Movie,Series',
            'Recursive': 'true',
            'Fields': 'Genres,Tags,MediaStreams,RunTimeTicks',
            'Limit': limit,
            'UserId': self.user_id
        }

        response = requests.get(url, headers=self.headers, params=params)
        items = response.json().get('Items', [])

        show_list: list[Show] = []
        for item in items:
            show: Show = {
                "name": item.get("Name"),
                "properties": {
                    CategoryCriteria.GENRE: item.get('Genres')
                }
            }

            media_type = item.get('Type')

            if media_type not in ['Movie', 'Series']:
                continue

            if media_type == 'Movie':
                media_streams = item.get('MediaStreams', [])
                audio_languages = list({
                    stream.get('Language') for stream in media_streams
                    if stream.get('Type') == 'Audio' and stream.get('Language')
                })
                runtime_ticks = item.get('RunTimeTicks', 0)
                duration = runtime_ticks / 10_000_000 / 60 if runtime_ticks else None

                show['properties'][CategoryCriteria.TYPE] = ["movie"]
                show['properties'][CategoryCriteria.DURATION] = [duration, duration]
                show['properties'][CategoryCriteria.LANGUAGE] = audio_languages

            else:
                show['properties'][CategoryCriteria.TYPE] = ["series"]
                try:
                    self.set_series_info(item.get('Id'), show)
                except IndexError:
                    continue
            if show:
                show_list.append(show)

        return show_list

    def get_user_id_from_username(self) -> str | None:
        url = f"{self.base_url}/Users"

        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        users = response.json()
        for user in users:
            if user.get("Name") == self.username:
                return user.get("Id")

    def set_series_info(self, series_id, show: Show):
        url = f"{self.base_url}/Shows/{series_id}/Episodes"
        params = {
            'UserId': self.user_id,
            # 'Limit': 1,
            'Fields': 'MediaStreams,RunTimeTicks'
        }
        response = requests.get(url, headers=self.headers, params=params)
        episodes = response.json().get('Items', [])

        first_episode = episodes[0]
        media_streams = first_episode.get('MediaStreams', [])
        audio_languages = list({
            stream.get('Language') for stream in media_streams
            if stream.get('Type') == 'Audio' and stream.get('Language')
        })
        durations = [(ep.get('RunTimeTicks') / 10_000_000 / 60) for ep in episodes if ep.get('RunTimeTicks')]
        durations = durations if len(durations) else [0]
        show['properties'][CategoryCriteria.DURATION] = [min(durations), max(durations)]
        show['properties'][CategoryCriteria.LANGUAGE] = [i for i in set(audio_languages)]

    def load_shows(self) -> list[Show]:
        with open(self.show_file_path, "r", encoding="utf-8") as f:
            loaded_data = json.load(f)
        restored_shows: list[Show] = deserialize_enum_keys(loaded_data)
        return restored_shows

    def save_shows(self, shows):
        with open(self.show_file_path, "w", encoding="utf-8", ) as f:
            json.dump(shows, f, indent=4, ensure_ascii=False)

    # def get_parent_info(self, parent_id):
    #     url = f"{self.base_url}/Users/{self.user_id}/Views"
    #     r = requests.get(url, headers=self.headers)
    #     pprint.pprint(r.json().get('Items', []))


class ShowAnalyzer:

    def __init__(self, shows: list[Show]):
        self.shows = shows

    def get_available_properties(self) -> dict[CategoryCriteria, list[str | int | float]]:
        properties = defaultdict(list)
        for show in self.shows:
            for p in show['properties']:
                values = show['properties'][p]
                properties[p] = list(set(([*values, *properties[p]])))
        return properties


if __name__ == '__main__':
    b = JellyfinShowRetriever(
        os.getenv("JELLYFIN_URL"),
        os.getenv("JELLYFIN_API_KEY"),
        os.getenv("JELLYFIN_USERNAME")
    )
    shows_l = b.get_shows(1000)
    available_props = ShowAnalyzer(shows_l).get_available_properties()
    channel_maker = ChannelMaker(available_properties=available_props)
    channel_maker.make_channel_frame()
    created_channel = channel_maker.channel
    show_selector = ShowSelector(channel=created_channel, show_list=shows_l)
    show_selector.generate_schedules()
    pprint.pprint(show_selector.channel)
