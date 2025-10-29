import requests

EXPO_PUSH_URL = "https://exp.host/--/api/v2/push/send"

def send_push_notification(expo_token, title, body, data=None):
    payload = {
        "to": expo_token,
        "sound": "default",
        "title": title,
        "body": body,
        "data": data or {},
    }
    try:
        requests.post(EXPO_PUSH_URL, json=payload, timeout=5)
    except Exception as e:
        print("Error enviando push:", e)
