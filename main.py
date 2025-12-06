import os
import requests
import google.generativeai as genai

# إعداد مفتاح الذكاء الاصطناعي
GEMINI_KEY = os.environ.get("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

def get_ai_category(channel_name):
    """يسأل Gemini عن تصنيف القناة"""
    try:
        # نص الطلب المبسط
        prompt = f"Categorize this TV channel: '{channel_name}'. Return ONLY one word from: [Sports, Movies, News, Kids, General]. If unsure, return General."
        response = model.generate_content(prompt)
        return response.text.strip()
    except:
        return "General"

def check_link(url):
    """يفحص إذا كان الرابط يعمل بسرعة"""
    try:
        # نحاول الاتصال لمدة ثانيتين فقط
        response = requests.head(url, timeout=2)
        return response.status_code == 200
    except:
        return False

def process_m3u():
    print("Starting Magic...")
    
    with open("input.m3u", "r", encoding="utf-8") as f:
        lines = f.readlines()
    
    new_content = ["#EXTM3U\n"]
    current_name = ""
    
    for line in lines:
        line = line.strip()
        if line.startswith("#EXTINF"):
            # استخراج الاسم القديم (ما بعد الفاصلة)
            current_name = line.split(",")[-1].strip()
        
        elif line.startswith("http"):
            url = line
            # 1. فحص الرابط (هل يعمل؟)
            if check_link(url):
                # 2. سؤال الذكاء الاصطناعي
                category = get_ai_category(current_name)
                print(f"✅ Active: {current_name} -> {category}")
                
                # كتابة السطر الجديد مع التصنيف
                new_entry = f'#EXTINF:-1 group-title="{category}", {current_name}\n{url}\n'
                new_content.append(new_entry)
            else:
                print(f"❌ Dead Link: {current_name}")

    # حفظ الملف النهائي
    with open("playlist_active.m3u", "w", encoding="utf-8") as f:
        f.writelines(new_content)

if __name__ == "__main__":
    if not GEMINI_KEY:
        print("Error: No API Key found!")
    else:
        process_m3u()
