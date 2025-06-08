import json
import os

from dotenv import load_dotenv

from ersatz_builder import PseudoTVBuilder
from jellyfin_api import JellyfinClient

load_dotenv()

def save_jellyfin_shows():
    client = JellyfinClient(
        os.getenv("JELLYFIN_URL"),
        os.getenv("JELLYFIN_API_KEY"),
        os.getenv("JELLYFIN_USERNAME")
    )
    shows = client.get_shows()
    client.save_to_json(shows, os.path.join("data", "shows.json"))


def generate_channel():
    with open(os.path.join("data", "config.json"), 'r') as f:
        config = json.load(f)
    builder = PseudoTVBuilder(os.getenv("ERSATZ_URL"))
    builder.start(config)


if __name__ == '__main__':
    # save_jellyfin_shows()
    # llm call - un jour
    generate_channel()
