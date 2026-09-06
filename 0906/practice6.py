import os

from dotenv import load_dotenv
from google import genai
from telegram import Update
from telegram.constants import ChatAction, ChatType
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters

load_dotenv()

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

client = genai.Client(api_key=GEMINI_API_KEY)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == ChatType.PRIVATE:
        await update.message.reply_text("👋 你好！直接發送訊息即可與我對話。")
    else:
        await update.message.reply_text(
            f"👋 大家好！在群組中請 @{context.bot.username} 或回覆我的訊息來提問。"
        )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    raw_text = update.message.text
    chat_type = update.effective_chat.type
    bot_name = context.bot.username

    is_private = chat_type == ChatType.PRIVATE
    is_mentioned = bot_name and f"@{bot_name.lower()}" in raw_text.lower()
    is_reply_to_bot = (
        update.message.reply_to_message
        and update.message.reply_to_message.from_user
        and update.message.reply_to_message.from_user.id == context.bot.id
    )

    # 非私聊且沒有 @機器人 也沒有回覆機器人時，直接略過
    if not is_private and not is_mentioned and not is_reply_to_bot:
        return

    # 去除 @BotUsername，留下純問題文字
    clean_text = raw_text.replace(f"@{bot_name}", "").strip()
    if not clean_text:
        return

    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id, action=ChatAction.TYPING
    )

    # 呼叫 Gemini
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=clean_text,
        config={
            "system_instruction": "你是一個 Telegram 群組 AI 助理，請用繁體中文給出簡潔有條理的回答。"
        },
    )

    await update.message.reply_text(
        response.text or "抱歉，無法生成回應。"
    )


def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("🚀 Gemini 群組 Telegram Bot 運行中...")
    app.run_polling()


if __name__ == "__main__":
    main()
