import re
import time

from playwright.sync_api import sync_playwright


class PseudoTVBuilder:
    def __init__(self, url):
        self.browser = None
        self.context = None
        self.page = None
        self.url = url

    def start(self, data):
        with sync_playwright() as p:
            self.browser = p.chromium.launch(headless=False)
            self.context = self.browser.new_context()
            self.page = self.context.new_page()

            if "channel" in data:
                self.create_channel(data["channel"])

            for playlist_group in data["playlist_groups"]:
                self.create_playlist_group(playlist_group["name"])

                for playlist in playlist_group['playlists']:
                    self.create_playlist(playlist_group["name"], playlist["name"])
                    self.redirect_to_playlist_add_item_page(playlist_group["name"], playlist["name"])
                    for item in playlist['items']:
                        self.add_playlist_item(item)
                    self.page.get_by_role("button", name="Save Changes").click()

            self.context.close()
            self.browser.close()

    def create_channel(self, data):
        self.page.goto(f"{self.url}/channels/add")
        self.page.get_by_label("Name").fill(data["name"])
        self.page.get_by_role("button", name="Add Channel").click()
        time.sleep(1)

    def create_playlist_group(self, name):
        self.page.goto(f"{self.url}/media/playlists")
        self.page.get_by_role("textbox", name="Playlist Group Name").click()
        self.page.get_by_role("textbox", name="Playlist Group Name").fill(name)
        self.page.get_by_role("button", name="Add Playlist Group").click()
        time.sleep(1)

    def create_playlist(self, playlist_group_name, playlist_name):
        self.page.goto(f"{self.url}/media/playlists")
        self.page.get_by_role("textbox", name="Playlist Name").click()
        self.page.get_by_role("textbox", name="Playlist Name").fill(playlist_name)
        self.page.get_by_role("textbox", name="Playlist Group", exact=True).click()
        self.page.get_by_text(playlist_group_name).first.click()
        self.page.get_by_role("button", name="Add Playlist", exact=True).click()

        time.sleep(1)

    def redirect_to_playlist_add_item_page(self, playlist_group_name, playlist_name):
        self.page.goto(f"{self.url}/media/playlists")
        self.page.get_by_text(playlist_group_name).click()
        self.page.get_by_role("listitem").filter(
            has_text=f"{playlist_group_name} {playlist_name}"
        ).get_by_role("link").first.click()
        time.sleep(1)

    def add_playlist_item(self, item_name):
        self.page.get_by_role("button", name="Add Playlist Item").click()
        self.page.get_by_text("Collection Collection Type").click()
        self.page.get_by_text("Television Show").click()

        self.page.get_by_role("textbox", name="Television Show").click()
        self.page.get_by_role("textbox", name="Television Show").fill(item_name)
        time.sleep(1)
        self.page.get_by_role("textbox", name="Television Show").press("Enter")
        self.page.get_by_text("Chronological Playback Order").click()
        self.page.get_by_text("Season, Episode").click()
        time.sleep(1)

    def create_playout(self, channel_name, schedule_name):
        self.page.goto(f"{self.url}/playouts/add")
        self.page.get_by_role("textbox", name="Channel").click()
        self.page.get_by_text(f"- {channel_name}").click()
        self.page.get_by_role("textbox", name="Schedule").click()
        self.page.get_by_text(schedule_name).click()
        self.page.get_by_role("button", name="Add Playout").click()
        time.sleep(2)

    def create_schedule(self, name):
        self.page.goto(f"{self.url}/schedules/add")
        self.page.get_by_role("textbox", name="Name").fill(name)
        self.page.get_by_role("button", name="Add Schedule").click()
        time.sleep(1)

    def add_schedule_items(self, schedule_name, items):
        self.page.goto(f"{self.url}/schedules/")
        self.page.get_by_role("row", name=schedule_name).get_by_role("link").nth(1).click()

        for item in items:
            self.page.get_by_role("button", name="Add Schedule Item").click()
            self.page.get_by_text("Collection Collection Type").click()
            self.page.locator("div").filter(has_text="Television Show").nth(3).click()
            self.page.get_by_role("textbox", name="Television Show").fill(item["query"])
            time.sleep(1)
            self.page.get_by_role("textbox", name="Television Show").press("Enter")
            self.page.get_by_text("Shuffle").click()
            self.page.get_by_text("Season, Episode").click()
            self.page.get_by_text("One Playout Mode").click()
            self.page.locator("div").filter(has_text=re.compile(r"^Multiple$")).first.click()
            self.page.get_by_role("textbox", name="Multiple Count").fill(str(item["count"]))
            time.sleep(1)

        self.page.get_by_role("button", name="Save Changes").click()
        time.sleep(1)
