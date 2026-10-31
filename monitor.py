import os
import re
import sys
import time
import requests
from playwright.sync_api import sync_playwright

URL = "https://ctsa.utk.com.tw/CTSA/public/race/running_game.aspx"
INTERVAL = 30
RUN_MINUTES = int(os.environ.get("RUN_MINUTES", "340"))

TOKEN = os.environ["TELEGRAM_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]


def notify(msg):
    try:
        requests.post(
            f"https://api.telegram.org/bot{TOKEN}/sendMessage",
            data={"chat_id": CHAT_ID, "text": msg},
            timeout=10,
        )
    except Exception as e:
        print("通知失敗:", e, flush=True)


def clean(s):
    return re.sub(r"\s+", " ", s).strip()


def read_page(page):
    text = page.inner_text("body")
    m_race = re.search(r"即時賽事\s*(.*?)\s*即時檢錄項目", text, re.S)
    m_chk = re.search(r"即時檢錄項目\s*(.*?)\s*即時比賽項目", text, re.S)
    race = clean(m_race.group(1)) if m_race else ""
    checkin = clean(m_chk.group(1)) if m_chk else None
    return race, checkin


def main():
    end = time.time() + RUN_MINUTES * 60
    notify(f"監控已啟動,將持續約 {RUN_MINUTES} 分鐘")
    last = None
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        while time.time() < end:
            try:
                page.goto(URL, wait_until="networkidle", timeout=60000)
                race, checkin = read_page(page)
                print("檢錄:", checkin, flush=True)
                if checkin is None:
                    print("找不到「即時檢錄項目」區塊", flush=True)
                elif checkin != last:
                    if checkin:
                        prefix = "(目前) " if last is None else ""
                        notify(f"🏊 {prefix}檢錄開始\n{race}\n{checkin}")
                    last = checkin
            except Exception as e:
                print("讀取失敗:", e, flush=True)
            time.sleep(INTERVAL)
    notify("監控時間結束,需要的話請重新啟動")


if __name__ == "__main__":
    sys.exit(main())
