import os

from dotenv import load_dotenv

load_dotenv()
JELLYFIN_URL = os.getenv("JELLYFIN_URL")
JELLYFIN_API_KEY = os.getenv("JELLYFIN_API_KEY")
JELLYFIN_USERNAME = os.getenv("JELLYFIN_USERNAME")
ERSATZ_URL = os.getenv("ERSATZ_URL")
