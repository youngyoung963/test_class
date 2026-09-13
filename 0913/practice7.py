import os
import json
import asyncio
from dotenv import load_dotenv
from google import genai
from google.genai import types
from telegram import Bot

# 載入環境變數
load_dotenv()
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# 你的群組 ID
GROUP_CHAT_ID = -5552797411

# 初始化 Gemini 客戶端
client = genai.Client(api_key=GEMINI_API_KEY)

def analyze_customer_message(user_message: str) -> dict:
    """
    呼叫 Gemini 進行情緒分析並回傳 JSON 結構資料
    """
    system_instruction = """
    你是一位專業的 Telegram 線上客服情緒分析與應對助手。
    請分析客戶發送的訊息情緒，並特別注意台灣在地的口語語境與反諷語氣。
    
    情緒分類說明:
    - positive: 正向滿意
    - neutral: 一般詢問 / 中立
    - negative: 輕微不滿 / 抱怨
    - urgent_angry: 強烈憤怒 / 要求主管或退費
    
    如果客戶表達強烈不滿、投訴消保官、威脅退費或情緒極度憤怒，請將 requires_human_agent 設為 true。
    
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
        print(f"❌ Gemini API 分析失敗: {e}")
        return {
            "sentiment": "neutral",
            "confidence_score": 0.0,
            "requires_human_agent": False,
            "reasoning": "分析過程發生例外狀況",
            "suggested_reply": "您好,已收到您的訊息,請稍候專人為您服務。"
        }

async def send_to_group(message: str):
    """
    發送訊息到指定的群組
    """
    if not TELEGRAM_TOKEN:
        raise ValueError("請先確認 .env 內已設定 TELEGRAM_BOT_TOKEN")
    
    bot = Bot(token=TELEGRAM_TOKEN)
    
    try:
        # 發送訊息到群組
        await bot.send_message(
            chat_id=GROUP_CHAT_ID,
            text=message,
            parse_mode="HTML"  # 支援 HTML 格式
        )
        print(f"✅ 訊息已發送到群組 {GROUP_CHAT_ID}")
    except Exception as e:
        print(f"❌ 發送失敗: {e}")

def main():
    """
    主程式:分析客戶訊息並發送到群組
    """
    if not TELEGRAM_TOKEN or not GEMINI_API_KEY:
        raise ValueError("請先確認 .env 內已設定 TELEGRAM_BOT_TOKEN 與 GEMINI_API_KEY。")
    
    # 測試訊息列表
    test_messages = [
        "請問我的訂單 #883921 什麼時候會出貨呢?謝謝!",
        "你們的APP到底怎麼回事?一直閃退,付了錢什麼都不能用,再不處理我就找消保官!",
        "包裹收到了,包裝很完整,速度也很快~"
    ]
    
    print("=" * 60)
    print("🤖 開始進行客戶訊息情緒分析並發送到群組")
    print(f"📱 目標群組 ID: {GROUP_CHAT_ID}")
    print("=" * 60)
    
    for idx, user_message in enumerate(test_messages, 1):
        print(f"\n【訊息 {idx}】{user_message}")
        
        # 執行情緒分析
        analysis = analyze_customer_message(user_message)
        
        # 標記需要真人介入的情境
        sentiment_tag = {
            "positive": "😊 正向滿意",
            "neutral": "💬 一般中立",
            "negative": "⚠️ 輕微不滿",
            "urgent_angry": "🚨 緊急客訴"
        }.get(analysis.get("sentiment"), "💬 一般中立")
        
        reply_content = analysis.get("suggested_reply", "收到您的訊息,處理中。")
        
        # 組合要發送到群組的訊息
        if analysis.get("requires_human_agent"):
            group_message = (
                f"<b>【客服通知｜{sentiment_tag}｜需要專人介入】</b>\n\n"
                f"<b>客戶訊息:</b>\n{user_message}\n\n"
                f"<b>情緒分析:</b>\n"
                f"• 情緒: {analysis.get('sentiment')}\n"
                f"• 信心指數: {analysis.get('confidence_score'):.2f}\n"
                f"• 判斷依據: {analysis.get('reasoning')}\n\n"
                f"<b>建議回覆:</b>\n{reply_content}\n\n"
                f"⚠️ <b>系統已通知管理員/真人客服進線處理</b>"
            )
        else:
            group_message = (
                f"<b>【客服通知｜{sentiment_tag}】</b>\n\n"
                f"<b>客戶訊息:</b>\n{user_message}\n\n"
                f"<b>情緒分析:</b>\n"
                f"• 情緒: {analysis.get('sentiment')}\n"
                f"• 信心指數: {analysis.get('confidence_score'):.2f}\n\n"
                f"<b>建議回覆:</b>\n{reply_content}"
            )
        
        # 發送到群組
        asyncio.run(send_to_group(group_message))
        
        # 避免發送過快,稍作延遲
        import time
        time.sleep(1)
    
    print("\n" + "=" * 60)
    print("✅ 所有測試訊息已處理完成")
    print("=" * 60)

if __name__ == "__main__":
    main()