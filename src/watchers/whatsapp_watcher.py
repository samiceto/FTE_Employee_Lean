# whatsapp_watcher.py
import logging
import re
import time
from pathlib import Path

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

KEYWORDS = ["urgent", "help", "invoice"]  # add your keywords here


class WhatsAppWatcher:
    def __init__(
        self, vault_path: str = None, session_path: str = None, check_interval: int = 60
    ):
        if vault_path is None:
            vault_path = "/mnt/d/FTE_Employee/hackathon_zero/ai_employee_vault"
        self.vault_path = Path(vault_path)
        self.needs_action = self.vault_path / "Need_Action" / "whatsapp"
        self.needs_action.mkdir(parents=True, exist_ok=True)

        if session_path is None:
            session_path = str(Path(__file__).parent / "whatsapp_session")
        self.session_path = Path(session_path)
        self.session_path.mkdir(parents=True, exist_ok=True)

        self.check_interval = check_interval

    def start(self):
        with sync_playwright() as p:
            browser = p.chromium.launch_persistent_context(
                user_data_dir=str(self.session_path),
                headless=False,
                viewport={"width": 1280, "height": 720},
            )
            page = browser.new_page()
            logging.info("Launching Chromium (persistent session)...")
            page.goto("https://web.whatsapp.com")
            logging.info("Waiting for WhatsApp login or QR scan...")
            page.wait_for_selector(
                'div[role="grid"]', timeout=0
            )  # waits until chat list/grid is visible
            logging.info("✅ Logged in — chat list visible")
            self.monitor_loop(page)

    def monitor_loop(self, page):
        logging.info("Entering main monitoring loop...")
        while True:
            try:
                self.scan_chats(page)
            except PlaywrightTimeoutError:
                logging.warning("Timeout while scanning chats. Retrying...")
            time.sleep(self.check_interval)

    def scan_chats(self, page):
        logging.info("Scanning chat rows for unread messages...")
        chat_rows = page.query_selector_all('div[role="row"]')
        logging.info(f"Total chat rows detected: {len(chat_rows)}")

        any_match = False
        for row in chat_rows:
            # check for unread badge
            unread_badge = row.query_selector('span[aria-label*="unread message"]')
            if not unread_badge:
                continue  # skip read chats

            chat_name = row.query_selector("span[title]")  # chat contact or group name
            chat_name_text = chat_name.inner_text() if chat_name else "Unknown"
            logging.info(f"Opening chat to read message → {chat_name_text}")
            row.click()
            time.sleep(1)  # wait for messages to load

            # get last message text
            messages = page.query_selector_all("div.message-in, div.message-out")
            if not messages:
                continue
            last_msg = messages[-1].inner_text().strip()
            logging.info(f"Unread chat → {chat_name_text} | Preview: {last_msg}")

            matched_keywords = [
                kw
                for kw in KEYWORDS
                if re.search(rf"\b{kw}\b", last_msg, re.IGNORECASE)
            ]
            logging.info(f"Keywords found: {matched_keywords}")

            if matched_keywords:
                any_match = True
                # save debug screenshot
                timestamp = int(time.time())
                screenshot_path = self.needs_action / f"whatsapp_debug_{timestamp}.png"
                page.screenshot(path=str(screenshot_path))
                logging.info(f"Debug screenshot saved: {screenshot_path}")

                # save message text
                msg_file = self.needs_action / f"msg_{timestamp}.txt"
                with open(msg_file, "w", encoding="utf-8") as f:
                    f.write(
                        f"Chat: {chat_name_text}\nMessage: {last_msg}\nKeywords: {matched_keywords}"
                    )
                logging.info(f"Message saved for action: {msg_file}")

        if not any_match:
            logging.info("No unread chats matched keywords.")


if __name__ == "__main__":
    watcher = WhatsAppWatcher()
    watcher.start()
