import websocket
import json
import requests

GAS_URL = "あなたのGASのURL"

def on_message(ws, message):
    data = json.loads(message)

    if "comment" in data:
        payload = {
            "user": data["user_name"],
            "comment": data["comment"],
            "thread_key": extract_thread_key(data["comment"])
        }
        requests.post(GAS_URL, json=payload)

def extract_thread_key(comment):
    # 例：「@しお」などをスレッドキーにする
    if comment.startswith("@"):
        return comment.split(" ")[0]
    return "general"

def on_open(ws):
    print("Connected")

if __name__ == "__main__":
    ws = websocket.WebSocketApp(
        "wss://www.showroom-live.com/room/your_room_id",
        on_message=on_message,
        on_open=on_open
    )
    ws.run_forever()
