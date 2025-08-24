import os

from dotenv import load_dotenv

load_dotenv()
JELLYFIN_URL = os.getenv("JELLYFIN_URL")
JELLYFIN_API_KEY = os.getenv("JELLYFIN_API_KEY")
JELLYFIN_USERNAME = os.getenv("JELLYFIN_USERNAME")
ERSATZ_URL = os.getenv("ERSATZ_URL")
DATA_DIR = "data"
PLAYOUT_DIR = "output"
ERSATZTV_PLAYOUT_DIR = "/root/.local/share/playout"

SUPER_CATEGORIES = {
}
