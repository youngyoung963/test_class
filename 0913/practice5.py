import os
import json
from dotenv import load_dotenv
from google import genai
from google.genai import types

# 載入環境變數
load_dotenv()

# 1. 初始化 Gemini Client
client = genai.Client()

def analyze_customer_message(user_message: str) -> dict:
    """
    分析客戶訊息的情緒
    
    回傳的字典包含:
    - sentiment: 情緒類型 (positive, neutral, negative, urgent_angry)
    - confidence_score: 信心指數 (0.0 到 1.0)
    - requires_human_agent: 是否需要轉接真人 (True/False)
    - reasoning: 判斷理由
    - suggested_reply: 建議回覆內容
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
    
    請以 JSON 格式回覆，包含以下欄位:
    {
        "sentiment": "情緒類型(positive/neutral/negative/urgent_angry)",
        "confidence_score": 0.0到1.0的信心指數,
        "requires_human_agent": true或false,
        "reasoning": "判斷該情緒的簡短理由或關鍵字說明",
        "suggested_reply": "適合給該使用者的同理心回覆建議"
    }
    """

    # 2. 呼叫模型並要求 JSON 格式輸出
    response = client.models.generate_content(
        model="gemini-3.5-flash",
        contents=user_message,
        config=types.GenerateContentConfig(
            system_instruction=system_instruction,
            response_mime_type="application/json",
            temperature=0.1,  # 降低隨機性以提升分類穩定度
        ),
    )

    # 3. 解析 JSON 結果
    result = json.loads(response.text)
    return result

# 4. 測試執行
if __name__ == "__main__":
    test_messages = [
        "請問我的訂單 #883921 什麼時候會出貨呢?謝謝!",
       
    ]

    for msg in test_messages:
        print(f"\n--- 測試訊息: {msg} ---")
        analysis = analyze_customer_message(msg)
        
        # 使用字典的方式取值
        print(f"情緒標籤: {analysis['sentiment']}")
        print(f"信心指數: {analysis['confidence_score']}")
        print(f"轉接真人: {'是' if analysis['requires_human_agent'] else '否'}")
        print(f"判斷依據: {analysis['reasoning']}")
        print(f"建議回覆: {analysis['suggested_reply']}")
