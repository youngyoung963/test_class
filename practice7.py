#國堂 & Raspberry_機器人_群組
#-5339618596

import asyncio
import os
from dotenv import load_dotenv
from telegram import Bot

load_dotenv()
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
# 替換為你的群組 Chat ID（注意負號）
GROUP_CHAT_ID = "-5339618596"

async def main():
    bot = Bot(token=TELEGRAM_TOKEN)
    
    # 主動發送文字訊息給群組
    await bot.send_message(
        chat_id=GROUP_CHAT_ID,
        text="📢 大家好！這是來自機器人的主動推播通知。"
    )
    print("✅ 訊息發送成功！")

if __name__ == "__main__":
    asyncio.run(main())