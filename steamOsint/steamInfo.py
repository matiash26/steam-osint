import subprocess
import time
import urllib.request
from pathlib import Path
from .colors import *

import requests
from playwright.sync_api import sync_playwright


class SteamInfo:

    def __init__(
        self,
        chrome_path=r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        debug_port=9222,
        profile_name="chrome-steamhistory",
        timeout=300,
    ):
        self.chrome_path = Path(chrome_path)
        self.debug_port = debug_port
        self.profile = Path.home() / profile_name
        self.timeout = timeout

        self._url = "https://steamhistory.net/"

        self.headers = {
            "content-type": "application/json",
            "user-agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/151.0.0.0 Safari/537.36"
            ),
            "cookie": ""
        }

        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        self.chrome_process = None

    def fetch(self, option, steam_id=None):
        try:
            option_list = {
                "name": "0",
                "realName": "1",
                "url": "2"
            }

            if option not in option_list:
                raise ValueError(
                    f"Invalid option: {option}. "
                    f"Available options: {list(option_list.keys())}"
                )

            steam_id = steam_id or self.steam_id
            get_option = option_list[option]

            url = (
                f"{self._url}"
                f"id/{steam_id}/history"
                f"?type={get_option}"
                f"&offset=0"
                f"&limit=200"
                f"&search="
            )

            response = requests.get(
                url,
                headers=self.headers,
                timeout=self.timeout
            )

            response.raise_for_status()

            data = response.json()

            return data.get("data")

        except Exception as error:
            return None


    def chrome_debug_running(self):
        try:
            urllib.request.urlopen(
                f"http://127.0.0.1:{self.debug_port}/json/version",
                timeout=1
            )

            return True

        except Exception:
            return False

    def start_chrome(self):

        if self.chrome_debug_running():
            return

        if not self.chrome_path.exists():
            raise FileNotFoundError(
                f"Chrome was not found at: {self.chrome_path}"
            )

        self.profile.mkdir(
            parents=True,
            exist_ok=True
        )

        self.chrome_process = subprocess.Popen([
            str(self.chrome_path),
            f"--remote-debugging-port={self.debug_port}",
            f"--user-data-dir={self.profile}",
            "--start-maximized",
        ])

        for attempt in range(30):

            if self.chrome_debug_running():
                print(f"\n   {BR}[{YL}!{RS}]{YL}{YL } Chrome is ready.")
                return

            print(
                f"\n   {BR}[{YL}!{RS}]{YL}{YL} Waiting for Chrome... "
                f"{attempt + 1}/30"
            )

            time.sleep(1)

        raise RuntimeError(
            "Could not start Chrome in debug mode."
        )

    def connect(self):
        self.playwright = sync_playwright().start()

        self.browser = self.playwright.chromium.connect_over_cdp(
            f"http://127.0.0.1:{self.debug_port}"
        )

        if not self.browser.contexts:
            raise RuntimeError(
                "No Chrome browser context was found."
            )

        self.context = self.browser.contexts[0]

        if self.context.pages:
            self.page = self.context.pages[0]

        else:
            self.page = self.context.new_page()

    def open_page(self):
        self.page.goto(
            self._url,
            wait_until="domcontentloaded",
            timeout=self.timeout * 1000
        )

    def wait_page(self):
        print(f"\n   {BR}[{YL}!{RS}]{YL}{YL} Don't close your Chrome.")
        try:
            self.page.wait_for_load_state(
                "networkidle",
                timeout=30000
            )

        except Exception:
            return
        time.sleep(2)

    def get_cookies(self):
        cookies = self.context.cookies(
            ["https://steamhistory.net"]
        )

        cookie_string = "; ".join(
            f'{cookie["name"]}={cookie["value"]}'
            for cookie in cookies
        )

        self.headers["cookie"] = cookie_string

        return cookie_string

    def close_chrome(self):
        try:
            if self.browser:
                self.browser.close()

        except Exception:
            pass

        try:
            if self.playwright:
                self.playwright.stop()

        except Exception:
            pass

        if self.chrome_process:

            try:
                self.chrome_process.terminate()
                self.chrome_process.wait(timeout=10)

            except Exception:

                try:
                    self.chrome_process.kill()

                except Exception:
                    pass

            self.chrome_process = None

    def run(self, steamId):
        try:
            if not self.headers.get("cookie"):
                self.start_chrome()
                self.connect()
                self.open_page()
                self.wait_page()
                self.get_cookies()

            name =  self.fetch("name", steamId)
            realName =  self.fetch("realName", steamId)
            url = self.fetch("url", steamId)
            
            return {
                "name": name or [],
                "realName": realName or [],
                "url": url or []
                }
        
        finally:
            self.close_chrome()