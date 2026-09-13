import os
import json
import logging
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from google import genai
from google.genai import types
from telegram import Update
from telegram.constants import ChatAction, ChatType
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters
import openpyxl
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill

# 載入環境變數
load_dotenv()
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")



# 設定 Logging 以便追蹤與除錯
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# 初始化 Gemini 客戶端
client = genai.Client(api_key=GEMINI_API_KEY)

# 建立記錄資料夾
LOGS_DIR = Path(__file__).parent / "chat_logs"
LOGS_DIR.mkdir(exist_ok=True)

def get_today_xlsx_path() -> Path:
    """取得今天的 xlsx 檔案路徑"""
    today = datetime.now().strftime("%Y-%m-%d")
    return LOGS_DIR / f"chat_log_{today}.xlsx"

def init_xlsx_file(filepath: Path):
    """初始化 xlsx 檔案,建立表頭"""
    wb = Workbook()
    ws = wb.active
    ws.title = "對話記錄"
    
    # 設定表頭
    headers = [
        "時間", "使用者名稱", "使用者ID", "聊天類型", 
        "原始訊息", "情緒", "信心指數", "需要真人", 
        "判斷依據", "建議回覆", "實際回覆"
    ]
    
    # 寫入表頭並設定樣式
    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col, value=header)
        cell.font = Font(bold=True, size=12)
        cell.fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
        cell.font = Font(bold=True, size=12, color="FFFFFF")
        cell.alignment = Alignment(horizontal="center", vertical="center")
    
    # 設定欄寬
    ws.column_dimensions['A'].width = 20  # 時間
    ws.column_dimensions['B'].width = 15  # 使用者名稱
    ws.column_dimensions['C'].width = 12  # 使用者ID
    ws.column_dimensions['D'].width = 12  # 聊天類型
    ws.column_dimensions['E'].width = 40  # 原始訊息
    ws.column_dimensions['F'].width = 12  # 情緒
    ws.column_dimensions['G'].width = 10  # 信心指數
    ws.column_dimensions['H'].width = 10  # 需要真人
    ws.column_dimensions['I'].width = 40  # 判斷依據
    ws.column_dimensions['J'].width = 40  # 建議回覆
    ws.column_dimensions['K'].width = 40  # 實際回覆
    
    wb.save(filepath)
    logger.info(f"✅ 已建立新的記錄檔: {filepath}")

def save_to_xlsx(
    user_name: str,
    user_id: int,
    chat_type: str,
    original_message: str,
    analysis: dict,
    actual_reply: str
):
    """儲存對話記錄到 xlsx"""
    try:
        filepath = get_today_xlsx_path()
        
        # 如果檔案不存在,先建立
        if not filepath.exists():
            init_xlsx_file(filepath)
        
        # 開啟檔案
        wb = openpyxl.load_workbook(filepath)
        ws = wb.active
        
        # 找到下一個空白列
        next_row = ws.max_row + 1
        
        # 寫入資料
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        data = [
            now,
            user_name,
            user_id,
            chat_type,
            original_message,
            analysis.get("sentiment", ""),
            analysis.get("confidence_score", 0.0),
            "是" if analysis.get("requires_human_agent") else "否",
            analysis.get("reasoning", ""),
            analysis.get("suggested_reply", ""),
            actual_reply
        ]
        
        for col, value in enumerate(data, 1):
            cell = ws.cell(row=next_row, column=col, value=value)
            cell.alignment = Alignment(wrap_text=True, vertical="top")
        
        # 儲存檔案
        wb.save(filepath)
        logger.info(f"✅ 已記錄到 xlsx: {filepath.name} (第 {next_row} 列)")
        
    except Exception as e:
        logger.error(f"❌ 儲存 xlsx 失敗: {e}")

# 定義情緒分析函式
def analyze_customer_message(user_message: str) -> dict:
    """
    呼叫 Gemini 進行情緒分析並回傳 JSON 結構資料
    """
    system_instruction = """
    你是一位專業的 Telegram 線上客服情緒分析與應對助手。
    請分析客戶發送的訊息情緒,並特別注意台灣在地的口語語境與反諷語氣。
    
    情緒分類說明:
    - positive: 正向滿意
    - neutral: 一般詢問 / 中立
    - negative: 輕微不滿 / 抱怨
    - urgent_angry: 強烈憤怒 / 要求主管或退費
    
    如果客戶表達強烈不滿、投訴消保官、威脅退費或情緒極度憤怒,請將 requires_human_agent 設為 true。
    
    請務必以繁體中文撰寫 reasoning 與 suggested_reply,並輸出符合以下結構的 JSON 格式:
    {
        "sentiment": "positive | neutral | negative | urgent_angry",
        "confidence_score": 0.0到1.0的浮點數,
        "requires_human_agent": true 或 false,
        "reasoning": "判斷該情緒的簡短理由",
        "suggested_reply": "適合同理客戶的建議回覆內容"
    }
    """
    try:
        response = client.models.generate_content(
            model="gemini-3.5-flash",
            contents=user_message,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                response_mime_type="application/json",
                temperature=0.1,
            ),
        )
        return json.loads(response.text)
    except Exception as e:
        logger.error(f"Gemini API 分析失敗: {e}")
        return {
            "sentiment": "neutral",
            "confidence_score": 0.0,
            "requires_human_agent": False,
            "reasoning": "分析過程發生例外狀況",
            "suggested_reply": "您好,已收到您的訊息,請稍候專人為您服務。"
        }

# 指令處理
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bot_info = await context.bot.get_me()
    if update.effective_chat.type == ChatType.PRIVATE:
        await update.message.reply_text(
            "👋 你好！我是客服情緒分析助手。\n\n"
            "發送訊息給我,我會:\n"
            "1️⃣ 分析您的訊息情緒\n"
            "2️⃣ 自動轉發分析結果到客服群組\n"
            "3️⃣ 提供建議的回覆內容\n"
            "4️⃣ 所有對話記錄會儲存在每日 xlsx 檔案中"
        )
    else:
        await update.message.reply_text(
            f"👋 大家好！我是客服情緒分析助手。\n"
            f"我會分析所有訊息並記錄在每日報表中。"
        )

# 訊息處理主邏輯
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    raw_text = update.message.text
    chat_type = update.effective_chat.type
    user = update.message.from_user

    # 取得機器人資訊
    bot_info = await context.bot.get_me()
    bot_name = bot_info.username or ""

    is_private = chat_type == ChatType.PRIVATE

    # 清除 @BotUsername 字串(如果有的話)
    clean_text = raw_text.replace(f"@{bot_name}", "", 1).strip()
    if not clean_text:
        clean_text = raw_text.strip()
    
    if not clean_text:
        return

    # 顯示「輸入中」狀態
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)

    # 執行情緒分析
    logger.info(f"分析訊息來自 {user.username or user.first_name}: {clean_text}")
    analysis = analyze_customer_message(clean_text)

    # 標記需要真人介入的情境
    sentiment_tag = {
        "positive": "😊 正向滿意",
        "neutral": "💬 一般中立",
        "negative": "⚠️ 輕微不滿",
        "urgent_angry": "🚨 緊急客訴"
    }.get(analysis.get("sentiment"), "💬 一般中立")

    reply_content = analysis.get("suggested_reply", "收到您的訊息,處理中。")

    # 回覆給使用者
    if analysis.get("requires_human_agent"):
        user_reply = (
            f"【{sentiment_tag}｜需要專人介入】\n"
            f"{reply_content}\n\n"
            f"（系統已通知管理員/真人客服進線處理）"
        )
    else:
        user_reply = reply_content

    await update.message.reply_text(
        user_reply,
        reply_to_message_id=update.message.message_id
    )

    # 儲存到 xlsx
    user_name = f"@{user.username}" if user.username else user.first_name or "未知使用者"
    chat_type_str = "私訊" if is_private else f"群組: {update.effective_chat.title or '未命名群組'}"
    
    save_to_xlsx(
        user_name=user_name,
        user_id=user.id,
        chat_type=chat_type_str,
        original_message=raw_text,
        analysis=analysis,
        actual_reply=user_reply
    )

def main():
    if not TELEGRAM_TOKEN or not GEMINI_API_KEY:
        raise ValueError("請先確認 .env 內已設定 TELEGRAM_BOT_TOKEN 與 GEMINI_API_KEY。")

    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("=" * 60)
    logger.info("🚀 Telegram 客服情緒分析 Bot 運行中...")
    logger.info(f"📊 記錄資料夾: {LOGS_DIR.absolute()}")
    logger.info(f"📄 今日記錄檔: {get_today_xlsx_path().name}")
    logger.info("=" * 60)
    
    app.run_polling()

if __name__ == "__main__":
    main()