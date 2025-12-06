import os
import requests
import google.generativeai as genai
import time

# --- إعدادات ---
MAX_CHANNELS_TO_TEST = 100  # سنفحص أول 100 قناة فقط للتجربة (يمكنك زيادة الرقم لاحقاً)
TIMEOUT_SECONDS = 3         # مدة انتظار استجابة القناة

# مفتاح الذكاء الاصطناعي
GEMINI_KEY = os.environ.get("GEMINI_API_KEY")

if GEMINI_KEY:
    genai.configure(api_key=GEMINI_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')

def get_ai_category(channel_name):
    """يسأل Gemini عن تصنيف القناة"""
    if not GEMINI_KEY: return "Uncategorized"
    try:
        # تأخير بسيط لتجنب الحظر
        time.sleep(1) 
        prompt = f"Categorize this TV channel: '{channel_name}'. Return ONLY one word from: [Sports, Movies, News, Kids, Religious, Documentary, General]. If unsure, return General."
        response = model.generate_content(prompt)
        return response.text.strip()
    except:
        return "General"

def check_stream(url):
    """يفحص إذا كان رابط الفيديو يعمل"""
    try:
        response = requests.head(url, timeout=TIMEOUT_SECONDS)
        return response.status_code >= 200 and response.status_code < 400
    except:
        return False

def parse_remote_playlist(playlist_url):
    """يقوم بتنزيل قائمة القنوات واستخراج الروابط منها"""
    channels = []
    try:
        print(f"📥 Downloading playlist: {playlist_url}...")
        response = requests.get(playlist_url, timeout=10)
        lines = response.text.splitlines()
        
        current_name = "Unknown"
        for line in lines:
            line = line.strip()
            if line.startswith("#EXTINF"):
                # محاولة استخراج الاسم
                parts = line.split(",")
                if len(parts) > 1:
                    current_name = parts[-1].strip()
            elif line.startswith("http") and not line.endswith(".m3u") and not line.endswith(".m3u8"):
                # وجدنا رابط فيديو مباشر!
                # ملاحظة: استثنينا .m3u لتجنب الدخول في دوامة قوائم لا نهائية
                channels.append({"name": current_name, "url": line})
            elif line.endswith(".m3u8"):
                 # m3u8 غالباً هو رابط بث مباشر، سنقبله
                 channels.append({"name": current_name, "url": line})
                 
    except Exception as e:
        print(f"⚠️ Error reading playlist {playlist_url}: {e}")
    
    return channels

def process_m3u():
    print("🚀 Starting Smart Processing...")
    
    # 1. قراءة ملف المصادر (input.m3u) لاستخراج روابط القوائم
    source_urls = []
    try:
        with open("input.m3u", "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith("http"):
                    source_urls.append(line)
    except FileNotFoundError:
        print("❌ Error: input.m3u not found!")
        return

    print(f"Found {len(source_urls)} source playlists.")

    # 2. استخراج القنوات من كل المصادر
    all_channels = []
    for source in source_urls:
        extracted = parse_remote_playlist(source)
        all_channels.extend(extracted)
        print(f"   -> Extracted {len(extracted)} channels from source.")
        
        # حماية من العدد الكبير جداً
        if len(all_channels) > MAX_CHANNELS_TO_TEST * 2:
            break

    print(f"Total raw channels found: {len(all_channels)}")
    print(f"🔍 Testing top {MAX_CHANNELS_TO_TEST} channels with AI...")

    # 3. الفحص والتصنيف
    final_playlist = ["#EXTM3U\n"]
    count = 0
    
    for channel in all_channels:
        if count >= MAX_CHANNELS_TO_TEST:
            break
            
        url = channel["url"]
        name = channel["name"]
        
        # هل القناة تعمل؟
        if check_stream(url):
            # الذكاء الاصطناعي يحدد الفئة
            category = get_ai_category(name)
            
            print(f"✅ [{count+1}] Alive: {name} -> {category}")
            
            entry = f'#EXTINF:-1 group-title="{category}", {name}\n{url}\n'
            final_playlist.append(entry)
            count += 1
        else:
            print(f"❌ Dead: {name}")

    # 4. حفظ الملف النهائي
    with open("playlist_active.m3u", "w", encoding="utf-8") as f:
        f.writelines(final_playlist)
    
    print("🎉 Done! Check 'playlist_active.m3u'.")

if __name__ == "__main__":
    process_m3u()
