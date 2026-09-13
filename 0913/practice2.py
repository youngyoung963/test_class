# 國堂_LV名牌包_打到骨折_channel

import asyncio
import os
from dotenv import load_dotenv
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode

load_dotenv()
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")

# 設定推播目標
TARGET_USER_ID = 774133156
TARGET_GROUP_ID = -5552797411
TARGET_CHANNEL_ID = -1004322810613

async def send_photo_broadcast(
    chat_id: str | int,
    photo_source: str,
    caption: str,
    keyboard: InlineKeyboardMarkup | None = None
):
    """
    發送帶有排版說明的圖片推播
    :param photo_source: 圖片網址 (URL) 或 本地圖片路徑
    :param caption: 說明文字 (上限 1024 字元)
    :param keyboard: 訊息底部的按鈕 (選填)
    """
    bot = Bot(token=TELEGRAM_TOKEN)
    try:
        # 若傳入本地檔案路徑，以二進位讀取發送；若為 URL 則直接傳入字串
        if os.path.exists(photo_source):
            with open(photo_source, "rb") as photo_file:
                await bot.send_photo(
                    chat_id=chat_id,
                    photo=photo_file,
                    caption=caption,
                    parse_mode=ParseMode.HTML,
                    reply_markup=keyboard
                )
        else:
            await bot.send_photo(
                chat_id=chat_id,
                photo=photo_source,
                caption=caption,
                parse_mode=ParseMode.HTML,
                reply_markup=keyboard
            )
        print(f"✅ 成功發送圖文至：{chat_id}")
    except Exception as e:
        print(f"❌ 發送至 {chat_id} 失敗：{e}")

async def main():
    # 1. 圖片來源（使用本地圖片，路徑相對於此腳本所在目錄）
    image_url = os.path.join(os.path.dirname(__file__), "assets", "lv1.png")

    # 2. HTML 排版內文 (注意：caption 限制上限 1024 字元)
    caption_text = (
        "🔥 <b>【限時下殺】LV Neverfull 經典老花托特包 打到骨折！</b>\n\n"
        "專櫃熱銷爆款，限量釋出只有 3 顆！\n\n"
        "▫️ <b>成色狀況：</b> 95 新極美品\n"
        "▫️ <b>專櫃售價：</b> <s>NT$ 86,000</s>\n"
        "▫️ <b>骨折特價：</b> <b>NT$ 29,800</b> 💥\n\n"
        "<i>配件完整附防塵袋、保證卡，提供正品檢驗保證。</i>\n\n"
        "#精品特賣 #LV #Neverfull #限時優惠"
    )

    # 3. 底部互動按鈕 (選填，可導向客服私訊或外部賣場)
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🛍️ 立即下單", url="https://t.me/Guotang_LV"),
            InlineKeyboardButton("💬 聯絡店長", url="https://t.me/Guotang_LV")
        ]
    ])

    targets = [
        TARGET_USER_ID,
        TARGET_GROUP_ID,
        TARGET_CHANNEL_ID
    ]

    for chat_id in targets:
        await send_photo_broadcast(chat_id, image_url, caption_text, keyboard)

if __name__ == "__main__":
    asyncio.run(main())