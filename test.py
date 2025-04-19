import base64
import requests
from email.mime.text import MIMEText

# === 基本設定 ===
access_token = "ya29.a0AZYkNZjJuqkMDY6yWlh4wNNnwTste6pu1t_8C0as7ZXcqTIGefuFi2D1mVageqH9-JHnkjE4-npY2Vz-zpnwOwB0CP2ztEbqMRQVZNHyqmD7wadi0vjgOs1Dym8LZEsvIB4CTcgjs4N-srBB-0Ra0M48VVFe2_yCaEYRvtLZaCgYKAS4SARYSFQHGX2Mi8klhCEsV5hkVGI86M1GWLg0175"
from_email = "no-reply@etoehotel.com"
to_email = "ikuta@montegrouphotel.com"
subject = "測試郵件"
body_text = "測試測試測試測試"

# === 組合 MIME 郵件 ===
message = MIMEText(body_text)
message["to"] = to_email
message["from"] = from_email
message["subject"] = subject

# === 編碼為 base64url ===
encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

# === 發送請求 ===
url = "https://gmail.googleapis.com/gmail/v1/users/me/messages/send"
headers = {
    "Authorization": f"Bearer {access_token}",
    "Content-Type": "application/json"
}
payload = {
    "raw": encoded_message
}

response = requests.post(url, headers=headers, json=payload)

# === 檢查結果 ===
if response.status_code == 200:
    print("郵件發送成功")
    print("Message ID:", response.json()["id"])
else:
    print("發送失敗:", response.status_code)
    print(response.json())

