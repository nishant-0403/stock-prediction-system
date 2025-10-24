# Notifications module: polls for signals and sends Telegram messages (skeleton)
import os
import time
import requests
from telegram import Bot

TELEGRAM_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
bot = Bot(token=TELEGRAM_TOKEN) if TELEGRAM_TOKEN else None

def send_message(chat_id, text):
    if not bot:
        print('No bot token configured. Message would be:', text)
        return
    bot.send_message(chat_id=chat_id, text=text)

def poll_and_notify():
    # Stub: in real system you subscribe to signals or consume from a queue.
    while True:
        # Example: get signals from backend or ML service
        try:
            resp = requests.get('http://localhost:8000/signals', timeout=5)
            signals = resp.json()
            for sig in signals:
                send_message(sig.get('chat_id', ''), f"Signal: {sig.get('text')}")
        except Exception as e:
            print('poll error', e)
        time.sleep(30)

if __name__ == '__main__':
    poll_and_notify()
