import requests
from flask import Flask, request

app = Flask(__name__)

# الإعدادات السرية لـ Meta (فيسبوك مسنجر)
VERIFY_TOKEN = "ROYAL_CHAUSSURES_SECRET_2026"
PAGE_ACCESS_TOKEN = "EAASvxCcZCEgkBR5vZB7cbYVLJXfQZBPbwQLHdBqVXGBhjZB2YhiaJqiAv7sJ8dAlh4UYvIaTPZA54hkZB9rewZAclgtC0Ah5Yjj1mNqGfndD1ZCSU83xPWbSd1bYxxAag9RH0pQqmj7PSevE4ZABFMQIAHbFG2ZATE1sus36RGPQUAVGiz71pwE7QNCNil0JASyldpNKMzVkk3yMhSJUZCHlO2VkAZDZD"

# رابط بوابة OpenClaw القياسي المفتوح على جهازك
OPENCLAW_API_URL = "http://127.0.0.1:18789/v1/chat/completions"

# الـ Token الصحيح الخاص بك
OPENCLAW_TOKEN = "40bc9bc11cee10397ec403a219f89274eac3682aa0a8a793"

def get_atlas_response(user_message, user_id):
    """إرسال رسالة الزبون إلى بوابة OpenClaw والحصول على رد ذكي من أطلس"""
    payload = {
        "model": "openclaw/main", # ⚡ الصيغة الرسمية الصحيحة لاستدعاء الـ Agent الخاص بك
        "messages": [
            {"role": "user", "content": user_message}
        ],
        "user": user_id 
    }
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {OPENCLAW_TOKEN}"
    }
    
    try:
        response = requests.post(OPENCLAW_API_URL, json=payload, headers=headers)
        if response.status_code == 200:
            result = response.json()
            ai_reply = result['choices'][0]['message']['content']
            return ai_reply
        else:
            print(f"⚠️ بوابة OpenClaw ردت برمز خطأ: {response.status_code}")
            print("تفاصيل رد السيرفر:", response.text)
            return "نعتذر منك، واجهنا مشكلة تقنية مؤقتة. يرجى المحاولة بعد قليل."
    except Exception as e:
        print("❌ فشل الاتصال ببوابة OpenClaw:", e)
        return "مرحباً بك في Royal Chaussures! جاري تحضير الرد من قبل خدمة العملاء."

def send_message_to_facebook(recipient_id, text_message):
    """إرسال الرد النهائي إلى الزبون عبر فيسبوك مسنجر"""
    url = f"https://graph.facebook.com/v20.0/me/messages?access_token={PAGE_ACCESS_TOKEN}"
    payload = {
        "recipient": {"id": recipient_id},
        "message": {"text": text_message}
    }
    headers = {"Content-Type": "application/json"}
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        return response.json()
    except Exception as e:
        print("❌ خطأ أثناء الإرسال إلى فيسبوك:", e)
        return None

@app.route('/webhook', methods=['GET'])
def verify_webhook():
    mode = request.args.get('hub.mode')
    token = request.args.get('hub.verify_token')
    challenge = request.args.get('hub.challenge')
    
    if mode and token:
        if mode == 'subscribe' and token == VERIFY_TOKEN:
            return challenge, 200
        else:
            return "Forbidden", 403
    return "Invalid parameters", 400

@app.route('/webhook', methods=['POST'])
def handle_messages():
    data = request.get_json()
    
    if data.get('object') == 'page':
        for entry in data.get('entry', []):
            for messaging_event in entry.get('messaging', []):
                if messaging_event.get('message') and 'text' in messaging_event['message']:
                    sender_id = messaging_event['sender']['id']
                    user_message = messaging_event['message']['text']
                    
                    print(f"📩 زبون يرسل: {user_message}")
                    
                    # 1. استدعاء المساعد الذكي أطلس
                    ai_response = get_atlas_response(user_message, sender_id)
                    print(f"🤖 أطلس يجيب: {ai_response}")
                    
                    # 2. تمرير الرد التلقائي فوراً إلى مسنجر الزبون
                    send_message_to_facebook(sender_id, ai_response)
                    
    return "EVENT_RECEIVED", 200

if __name__ == '__main__':
    app.run(port=5000, debug=True)
