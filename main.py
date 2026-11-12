from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
import yt_dlp
import os
import uuid
import shutil

app = FastAPI(title="Video Downloader API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

downloads_status = {}
ffmpeg_path = shutil.which("ffmpeg")

# كود الواجهة الأمامية مدمج بالكامل هنا
HTML_CONTENT = """<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>محمل الفيديوهات - Video Downloader</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Tajawal:wght@300;400;500;700;800&display=swap" rel="stylesheet">
    <style> * { font-family: 'Tajawal', sans-serif; } </style>
</head>
<body class="bg-slate-950 text-slate-50 min-h-screen flex flex-col items-center justify-center p-4">
    <div class="max-w-xl w-full bg-slate-900 border border-slate-800 p-6 rounded-2xl shadow-2xl">
        <h1 class="text-2xl font-bold text-center mb-6 text-purple-400">محمل الفيديوهات السريع</h1>
        <div class="flex gap-2 mb-4">
            <input type="url" id="videoUrl" placeholder="الصق رابط الفيديو هنا (يوتيوب، تيك توك...)" class="flex-1 bg-slate-950 border border-slate-700 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-purple-500" dir="ltr">
            <button id="fetchBtn" class="bg-purple-600 hover:bg-purple-500 px-6 py-3 rounded-xl font-bold text-white transition">جلب</button>
        </div>
        <div id="result" class="text-center text-sm text-slate-400"></div>
    </div>
    <script>
        const API_BASE = '';
        document.getElementById('fetchBtn').onclick = async () => {
            const url = document.getElementById('videoUrl').value.trim();
            const resDiv = document.getElementById('result');
            if(!url) { alert('الرجاء إدخال الرابط'); return; }
            resDiv.textContent = 'جاري التحميل والمعالجة...';
            try {
                const response = await fetch(`${API_BASE}/api/download-simple`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ url })
                });
                const data = await response.json();
                if(response.ok) {
                    resDiv.innerHTML = `<span class="text-green-400 font-bold">تم التحميل بنجاح! اسم الملف: ${data.filename}</span>`;
                } else {
                    resDiv.innerHTML = `<span class="text-red-400">${data.detail}</span>`;
                }
            } catch(e) {
                resDiv.innerHTML = `<span class="text-red-400">حدث خطأ في الاتصال</span>`;
            }
        };
    </script>
</body>
</html>"""

@app.get("/", response_class=HTMLResponse)
async def serve_frontend():
    return HTML_CONTENT

@app.post("/api/download-simple")
async def download_simple(data: dict):
    url = data.get("url")
    if not url:
        raise HTTPException(status_code=400, detail="الرابط مطلوب")
    
    # إعدادات متقدمة لتجاوز حماية يوتيوب وتجنب خطأ الـ Bot
    ydl_opts = {
        'outtmpl': os.path.join(DOWNLOAD_DIR, '%(title)s.%(ext)s'),
        'format': 'best',
        'quiet': True,
        'extractor_args': {
            'youtube': {
                'player_client': ['android', 'web']
            }
        },
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
        }
    }
    if ffmpeg_path:
        ydl_opts['ffmpeg_location'] = os.path.dirname(ffmpeg_path)

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            return {"status": "success", "filename": os.path.basename(filename)}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
