#國堂_LV名牌包_打到骨折_channel
#-4322810613

import asyncio
import os
from dotenv import load_dotenv
from telegram import Bot

load_dotenv()
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")

# 設定不同推播目標
TARGET_USER_ID = 8719067870               # 個人 (正整數，用戶需先私訊過 Bot)
TARGET_GROUP_ID = "-5339618596"         # 群組 (負整數，Bot 需在群組內)
TARGET_CHANNEL = "@國堂_LV名牌包_打到骨折_channel"      # 頻道 (公開填 @帳號，Bot 需為管理員)

async def send_broadcast(chat_id: str | int, message: str):
    bot = Bot(token=TELEGRAM_TOKEN)
    try:
        await bot.send_message(chat_id=chat_id, text=message)
        print(f"✅ 成功發送至：{chat_id}")
    except Exception as e:
        print(f"❌ 發送至 {chat_id} 失敗：{e}")

async def main():
    text = "📢 大家好！這是來自 Telegram Bot 的跨平台主動推播通知。"

    # 可同時推送給多個目標
    targets = [
        TARGET_USER_ID,
        TARGET_GROUP_ID,
        TARGET_CHANNEL,
    ]

    for chat_id in targets:
        await send_broadcast(chat_id, text)

if __name__ == "__main__":
    asyncio.run(main())