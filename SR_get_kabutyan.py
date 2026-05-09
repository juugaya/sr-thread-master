import websocket
import json
import requests
import time
import threading
from queue import Queue

# ▼ 監視したい SHOWROOM URL を複数指定（/r/ は消す）
ROOM_URLS = [
    "https://www.showroom-live.com/48_KABUTAKE_MANA",
    "https://www.showroom-live.com/48_MIYOSHI_MAAYA",
]

# ▼ GAS URL
GAS_URL = "https://script.google.com/macros/s/1Pz7E_vPQU6mfI5gaWXToklBaVwT5J0sinAuc7eVKNo0/exec"

# -------------------------
# 高速化：セッション + 非同期キュー
# -------------------------
session = requests.Session()
session.headers.update({"Content-Type": "application/json"})
send_queue = Queue()

def gas_worker():
    while True:
        payload = send_queue.get()
        try:
            session.post(GAS_URL, data=json.dumps(payload), timeout=1.5)
        except:
            try:
                session.post(GAS_URL, data=json.dumps(payload), timeout=1.5)
            except:
                pass
        send_queue.task_done()

threading.Thread(target=gas_worker, daemon=True).start()

# -------------------------
# room_id 取得
# -------------------------
def get_room_id(url):
    api = "https://www.showroom-live.com/api/live/live_info?room_url_key="
    key = url.split("/")[-1]
    res = session.get(api + key, timeout=2).json()

    if "room_id" not in res:
        print("❌ room_id が取得できません:", res)
        raise ValueError("URL が正しくない可能性があります")

    return res["room_id"]

# -------------------------
# WebSocket 1本分の処理
# -------------------------
def run_ws(room_url):
    room_key = room_url.split("/")[-1]
    room_id = get_room_id(room_url)
    ws_url = f"wss://www.showroom-live.com/api/live/comment_stream?room_id={room_id}"

    print(f"▶ {room_key} の WebSocket を開始（room_id={room_id}）")

    def on_message(ws, message):
        data = json.loads(message)
        if data.get("t") == 1:
            user = data["u"]["n"]
            comment = data["cm"]
            ts = int(time.time() * 1000)

            # ▼ GAS に送信（room_key 付き）
            send_queue.put({
                "mode": "add_comment",
                "timestamp": ts,
                "user": user,
                "comment": comment,
                "room": room_key
            })

            print(f"[{room_key}] {user}: {comment}")

    def on_open(ws):
        print(f"[{room_key}] CONNECTED")

    def on_error(ws, error):
        print(f"[{room_key}] ERROR:", error)

    def on_close(ws, code, msg):
        print(f"[{room_key}] CLOSED:", code, msg)

    while True:
        try:
            ws = websocket.WebSocketApp(
                ws_url,
                on_open=on_open,
                on_message=on_message,
                on_error=on_error,
                on_close=on_close
            )
            ws.run_forever(ping_interval=30, ping_timeout=10)
        except Exception as e:
            print(f"[{room_key}] Exception:", e)

        print(f"[{room_key}] Reconnecting in 5 seconds...")
        time.sleep(5)

# -------------------------
# ルームごとにスレッド起動
# -------------------------
for url in ROOM_URLS:
    threading.Thread(target=run_ws, args=(url,), daemon=True).start()

# メインスレッドは待機
while True:
    time.sleep(1)
