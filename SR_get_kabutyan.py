import websocket
import json
import requests
import time
import threading
from queue import Queue

# -------------------------
# 設定
# -------------------------
SHOWROOM_URL = "https://www.showroom-live.com/r/48_KABUTAKE_MANA"
GAS_URL = "https://script.google.com/macros/s/1Pz7E_vPQU6mfI5gaWXToklBaVwT5J0sinAuc7eVKNo0/exec"

# -------------------------
# 高速化：requests.Session を使う
# -------------------------
session = requests.Session()
session.headers.update({"Content-Type": "application/json"})

# 送信用キュー
send_queue = Queue()

# -------------------------
# GAS 送信ワーカー（非同期）
# -------------------------
def gas_worker():
    while True:
        payload = send_queue.get()
        try:
            session.post(
                GAS_URL,
                data=json.dumps(payload),
                timeout=1.5  # 高速化ポイント
            )
        except Exception:
            # 失敗したら 1 回だけ再送
            try:
                session.post(GAS_URL, data=json.dumps(payload), timeout=1.5)
            except:
                pass
        send_queue.task_done()

# ワーカー起動
threading.Thread(target=gas_worker, daemon=True).start()

# -------------------------
# SHOWROOM room_id 取得
# -------------------------
def get_room_id(url):
    api = "https://www.showroom-live.com/api/live/live_info?room_url_key="
    key = url.split("/")[-1]
    res = session.get(api + key, timeout=2).json()
    return res["room_id"]

room_id = get_room_id(SHOWROOM_URL)
ws_url = f"wss://www.showroom-live.com/api/live/comment_stream?room_id={room_id}"

# -------------------------
# WebSocket コールバック
# -------------------------
def on_message(ws, message):
    data = json.loads(message)

    if data.get("t") == 1:
        user = data["u"]["n"]
        comment = data["cm"]
        ts = int(time.time() * 1000)

        # GAS 送信をキューに積む（高速）
        send_queue.put({
            "mode": "add_comment",
            "timestamp": ts,
            "user": user,
            "comment": comment
        })

        print(f"{user}: {comment}")

def on_open(ws):
    print("WebSocket CONNECTED")

def on_error(ws, error):
    print("WebSocket ERROR:", error)

def on_close(ws, code, msg):
    print("WebSocket CLOSED:", code, msg)

# -------------------------
# 自動再接続ループ
# -------------------------
def connect_loop():
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
            print("WebSocket Exception:", e)

        print("Reconnecting in 5 seconds...")
        time.sleep(5)

if __name__ == "__main__":
    connect_loop()
