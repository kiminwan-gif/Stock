import os
import sys
import requests

# ── 설정 ──────────────────────────────────────────────
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

STOCKS = {
    "005930": "삼성전자",
    "000660": "SK하이닉스",
}
# ──────────────────────────────────────────────────────


def get_prices(codes):
    """네이버 금융 실시간 시세 API에서 현재가/등락률을 가져온다."""
    url = "https://polling.finance.naver.com/api/realtime/domestic/stock/" + ",".join(codes)
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Referer": "https://finance.naver.com/",
    }
    resp = requests.get(url, timeout=10, headers=headers)
    print(f"[디버그] HTTP 상태코드: {resp.status_code}")
    print(f"[디버그] 응답 내용(앞 500자): {resp.text[:500]}")
    resp.raise_for_status()
    data = resp.json()

    results = {}
    for item in data.get("datas", []):
        code = item.get("cd")
        results[code] = {
            "name": item.get("nm"),
            "price": item.get("nv"),        # 현재가
            "change": item.get("cv"),       # 전일 대비 변동
            "change_rate": item.get("cr"),  # 등락률(%)
            "rise_fall": item.get("rf"),    # 2:상승, 4:하락, 3:보합 등
        }
    return results


def build_message(prices):
    icon = {"2": "🔺", "4": "🔻", "3": "➖", "5": "🔺", "1": "🔺"}
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

    prices = get_prices(list(STOCKS.keys()))
    message = build_message(prices)
    send_telegram(message)
    print("전송 완료:\n" + message)


if __name__ == "__main__":
    main()
