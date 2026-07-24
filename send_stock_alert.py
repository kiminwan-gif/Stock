import os
import sys
from datetime import datetime, timezone, timedelta
import requests

# ── 설정 ──────────────────────────────────────────────
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
KST = timezone(timedelta(hours=9))

STOCKS = {
    "005930": "삼성전자",
    "000660": "SK하이닉스",
}
# ──────────────────────────────────────────────────────


def is_within_active_hours():
    """평일(월~금) 08:00~20:00(KST)인지 확인한다."""
    now = datetime.now(KST)
    is_weekday = now.weekday() < 5  # 0=월요일 ... 4=금요일
    is_active_hour = 8 <= now.hour < 20
    return is_weekday and is_active_hour


def get_prices(codes):
    """네이버 금융 실시간 시세 API에서 현재가/등락률을 가져온다."""
    url = "https://polling.finance.naver.com/api/realtime/domestic/stock/" + ",".join(codes)
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Referer": "https://finance.naver.com/",
    }
    resp = requests.get(url, timeout=10, headers=headers)
    resp.raise_for_status()
    data = resp.json()

    results = {}
    for item in data.get("datas", []):
        code = item.get("itemCode")
        compare = item.get("compareToPreviousPrice", {}) or {}
        results[code] = {
            "name": item.get("stockName"),
            "price": item.get("closePrice"),
            "change": item.get("compareToPreviousClosePrice"),
            "change_rate": item.get("fluctuationsRatio"),
            "rise_fall": compare.get("code"),
        }
    return results


def build_message(prices):
    icon = {"1": "🔺", "2": "🔺", "3": "➖", "4": "🔻", "5": "🔻"}
    lines = ["📈 주가 알림"]
    for code, name in STOCKS.items():
        info = prices.get(code)
        if not info:
            lines.append(f"{name}: 정보를 가져오지 못했습니다")
            continue
        arrow = icon.get(str(info["rise_fall"]), "")
        lines.append(
            f"{name}: {info['price']}원 {arrow} {info['change']} ({info['change_rate']}%)"
        )
    return "\n".join(lines)


def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    resp = requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": message}, timeout=10)
    resp.raise_for_status()


def main():
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("환경변수 TELEGRAM_TOKEN, TELEGRAM_CHAT_ID 가 설정되어 있지 않습니다.")
        sys.exit(1)

    if not is_within_active_hours():
        now = datetime.now(KST)
        print(f"[스킵] 현재 시각 {now.strftime('%Y-%m-%d %H:%M')} (KST)은 알림 대상 시간대가 아닙니다.")
        return

    prices = get_prices(list(STOCKS.keys()))
    message = build_message(prices)
    send_telegram(message)
    print("전송 완료:\n" + message)


if __name__ == "__main__":
    main()
