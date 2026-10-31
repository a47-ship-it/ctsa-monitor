import os
import sys
import time
import requests
from playwright.sync_api import sync_playwright

URL = "https://ctsa.utk.com.tw/CTSA/public/race/running_game.aspx"
KEYWORD = "檢錄中"
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


def find_rows(page):
    rows = page.eval_on_selector_all(
        "tr",
        "(els, kw) => els.filter(e => e.innerText.includes(kw))"
        ".map(e => e.innerText.replace(/\\s+/g, ' ').trim())",
        KEYWORD,
    )
    if rows:
        return rows
    text = page.inner_text("body")
    return [ln.strip() for ln in text.splitlines() if KEYWORD in ln]


def main():
    end = time.time() + RUN_MINUTES * 60
    notify(f"監控已啟動,將持續約 {RUN_MINUTES} 分鐘")
    seen = set()
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        while time.time() < end:
            try:
                page.goto(URL, wait_until="networkidle", timeout=60000)
                current = set(find_rows(page))
                for r in current - seen:
                    print("檢錄中:", r, flush=True)
                    notify("🏊 檢錄開始\n" + r)
                seen = current
            except Exception as e:
                print("讀取失敗:", e, flush=True)
            time.sleep(INTERVAL)
    notify("監控時間結束,需要的話請重新啟動")


if __name__ == "__main__":
    sys.exit(main())
