import os
import json
from datetime import datetime
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError
from google.oauth2.credentials import Credentials
from tenacity import retry, stop_after_attempt, wait_exponential
import re 

TMP = os.getenv("GITHUB_WORKSPACE", ".") + "/tmp"
VIDEO = os.path.join(TMP, "short.mp4")
THUMB = os.path.join(TMP, "thumbnail.png")
READY_VIDEO = os.path.join(TMP, "short_ready.mp4")
UPLOAD_LOG = os.path.join(TMP, "upload_history.json")

# 🔥 LEGION CHANNEL CONFIG
CHANNEL_NAME = "The 5AM Legion"
CHANNEL_TAGLINE = "Unleashing potential before sunrise 🔥"

# ---- Load Global Metadata ONCE ----
try:
    with open(os.path.join(TMP, "script.json"), "r", encoding="utf-8") as f:
        data = json.load(f)
except FileNotFoundError:
    print("❌ Error: script.json not found.")
    raise

title = data.get("title", "5AM Motivation")
description = data.get("description", f"{title}")
hashtags = data.get("hashtags", ["#motivation", "#selfimprovement", "#shorts"])
topic = data.get("topic", "motivation")

# ---- Step 1: Validate video ----
if not os.path.exists(VIDEO):
    raise FileNotFoundError(f"Video file not found: {VIDEO}")

video_size_mb = os.path.getsize(VIDEO) / (1024 * 1024)
print(f"📹 Motivational video file found: {VIDEO} ({video_size_mb:.2f} MB)")
if video_size_mb < 0.1:
    raise ValueError("Video file is too small, likely corrupted")

# ---- Step 2: Rename video to safe filename ----
safe_title = re.sub(r'[^\w\s-]', '', title).strip().replace(' ', '_')
video_output_path = os.path.join(TMP, f"{safe_title}.mp4")

if VIDEO != video_output_path:
    if os.path.exists(VIDEO):
        try:
            os.rename(VIDEO, video_output_path)
            VIDEO = video_output_path
            print(f"🎬 Final motivational video renamed to: {video_output_path}")
        except Exception as e:
            print(f"⚠️ Renaming failed: {e}. Using original path.")
    else:
        print("⚠️ Video file not found before rename.")
else:
    print("🎬 Video already has the correct filename.")

# ---- Step 3: Authenticate ----
try:
    creds = Credentials(
        None,
        refresh_token=os.getenv("GOOGLE_REFRESH_TOKEN"),
        token_uri="https://oauth2.googleapis.com/token",
        client_id=os.getenv("GOOGLE_CLIENT_ID"),
        client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
        scopes=["https://www.googleapis.com/auth/youtube.upload"]
    )
    youtube = build("youtube", "v3", credentials=creds, cache_discovery=False)
    print("✅ YouTube API authenticated")
except Exception as e:
    print(f"❌ Authentication failed: {e}")
    raise

# ---- Step 4: 🔥 Prepare LEGION-OPTIMIZED metadata ----
# Enhanced description with motivational CTAs and keywords
enhanced_description = f"""{description}

{' '.join(hashtags)}

🔥 {CHANNEL_TAGLINE}

---
📅 New motivation daily!
💪 Rise earlier, push harder, and unlock your full potential.
💚 Follow {CHANNEL_NAME} for daily motivation
🔥 Topics: Morning Routines • Success Habits • Mindset • Peak Performance

Join The 5AM Legion:
YouTube   : @The5AMLegion
Instagram : @The5AMLegion
TikTok    : @The5AMLegion
Facebook  : The 5AM Legion

Created: {datetime.now().strftime('%Y-%m-%d')}
Category: Self-Help & Motivation
"""

# 🔥 LEGION-SPECIFIC TAGS (optimized for discovery)
legion_base_tags = [
    "motivation",
    "motivational speech",
    "self improvement",
    "success mindset",
    "morning routine",
    "peak performance",
    "personal development",
    "discipline",
    "habit building",
    "mental strength",
    "motivation shorts",
    "success",
    "productivity",
    "mindset",
    "inspirational"
]

# Combine with script hashtags
tags = legion_base_tags.copy()
if hashtags:
    tags.extend([tag.replace('#', '').lower() for tag in hashtags[:10]])
tags.append("shorts")
tags.append("inspiring")

# Remove duplicates and limit to 15 tags (YouTube limit is 500 chars, ~15 tags is safe)
tags = list(dict.fromkeys(tags))[:15]

print(f"📝 Motivational metadata ready:")
print(f"   Title: {title}")
print(f"   Channel: {CHANNEL_NAME}")
print(f"   Tags: {', '.join(tags[:10])}...")
print(f"   Hashtags: {' '.join(hashtags[:5])}...")

snippet = {
    "title": title[:100],  # YouTube limit
    "description": enhanced_description[:5000],  # YouTube limit
    "tags": tags,
    "categoryId": "27"  # 🔥 Category 27 = "Education" (good for motivational content)
}

body = {
    "snippet": snippet,
    "status": {
        "privacyStatus": "public",
        "selfDeclaredMadeForKids": False,
        "madeForKids": False
    }
}

print(f"📤 Uploading motivational video to YouTube...")

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=2, min=4, max=60))
def upload_video(youtube_client, video_path, metadata):
    media = MediaFileUpload(
        video_path,
        chunksize=1024*1024,
        resumable=True,
        mimetype="video/mp4"
    )
    
    request = youtube_client.videos().insert(
        part="snippet,status",
        body=metadata,
        media_body=media
    )
    
    response = None
    last_progress = 0
    
    while response is None:
        status, response = request.next_chunk()
        if status:
            progress = int(status.progress() * 100)
            if progress != last_progress and progress % 10 == 0:
                print(f"⏳ Upload progress: {progress}%")
                last_progress = progress
    return response

try:
    print("🚀 Starting motivational video upload...")
    result = upload_video(youtube, VIDEO, body)
    video_id = result["id"]
    video_url = f"https://www.youtube.com/watch?v={video_id}"
    shorts_url = f"https://www.youtube.com/shorts/{video_id}"
    
    print(f"✅ Motivational video uploaded successfully!")
    print(f"   Video ID: {video_id}")
    print(f"   Watch URL: {video_url}")
    print(f"   Shorts URL: {shorts_url}")

except HttpError as e:
    print(f"❌ HTTP error during upload: {e}")
    error_content = e.content.decode() if hasattr(e, 'content') else str(e)
    print(f"   Error details: {error_content}")
    raise
except Exception as e:
    print(f"❌ Upload failed: {e}")
    raise

# ---- Step 6: Set thumbnail (desktop view) ----
if os.path.exists(THUMB):
    try:
        print("🖼️ Setting motivational thumbnail for desktop views...")
        thumb_size_mb = os.path.getsize(THUMB) / (1024*1024)
        if thumb_size_mb > 2:
            print(f"⚠️ Compressing thumbnail ({thumb_size_mb:.2f}MB)...")
        
        youtube.thumbnails().set(
            videoId=video_id, 
            media_body=MediaFileUpload(THUMB)
        ).execute()
        print("✅ Motivational thumbnail set successfully (desktop view).")
    except Exception as e:
        print(f"⚠️ Thumbnail upload failed: {e}")
else:
    print("⚠️ No thumbnail file found, skipping thumbnail set.")

# ---- Step 7: 🔥 Save upload history with LEGION analytics ----
upload_metadata = {
    "video_id": video_id,
    "title": title,
    "topic": topic,
    "channel": CHANNEL_NAME,
    "upload_date": datetime.now().isoformat(),
    "video_url": video_url,
    "shorts_url": shorts_url,
    "hashtags": hashtags,
    "file_size_mb": round(video_size_mb, 2),
    "tags": tags,
    "category": "Self-Help & Motivation",
    "content_type": "motivational_short"
}

history = []
if os.path.exists(UPLOAD_LOG):
    try:
        with open(UPLOAD_LOG, 'r') as f:
            history = json.load(f)
    except:
        history = []

history.append(upload_metadata)
history = history[-100:]  # Keep last 100 uploads

with open(UPLOAD_LOG, 'w') as f:
    json.dump(history, f, indent=2)

# 🔥 Analytics summary
total_uploads = len(history)
print(f"\n📊 Channel Stats: {total_uploads} motivational videos uploaded total")

print("\n" + "="*70)
print("🔥 MOTIVATIONAL VIDEO UPLOAD COMPLETE!")
print("="*70)
print(f"🔔 Channel: {CHANNEL_NAME}")
print(f"📹 Title: {title}")
print(f"🏷️  Topic: {topic}")
print(f"🆔 Video ID: {video_id}")
print(f"🔗 Shorts URL: {shorts_url}")
print(f"#️⃣  Hashtags: {' '.join(hashtags[:5])}")
print(f"🏷️  Tags: {', '.join(tags[:8])}...")
print("="*70)
print("\n💡 Motivational Channel Tips:")
print("   • Best posting time: 5-7 AM (peak morning motivation)")
print("   • Post consistently to build a routine")
print("   • Engage with comments within 1 hour for algorithm boost")
print("   • Cross-post to Instagram at 7 AM")
print(f"\n🔗 Share this URL: {shorts_url}")
print("🔥 Keep the Legion growing! 💪")