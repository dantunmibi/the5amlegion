import os
import json
from datetime import datetime
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from tenacity import retry, stop_after_attempt, wait_exponential
from PIL import Image
import re 

TMP = os.getenv("GITHUB_WORKSPACE", ".") + "/tmp"
VIDEO = os.path.join(TMP, "short.mp4")
THUMB = os.path.join(TMP, "thumbnail.png")
READY_VIDEO = os.path.join(TMP, "short_ready.mp4")
UPLOAD_LOG = os.path.join(TMP, "upload_history.json")

# 💪 5AM LEGION CHANNEL CONFIG
CHANNEL_NAME = "The 5AM Legion"
CHANNEL_TAGLINE = "Rise early. Dominate the day. 💪"

# ---- Load Global Metadata ONCE ----
try:
    with open(os.path.join(TMP, "script.json"), "r", encoding="utf-8") as f:
        data = json.load(f)
except FileNotFoundError:
    print("❌ Error: script.json not found.")
    raise

title = data.get("title", "Rise & Grind")
description = data.get("description", f"{title}")
hashtags = data.get("hashtags", ["#5AMClub", "#motivation", "#grindset", "#shorts"])
topic = data.get("topic", "motivation")
intensity = data.get("intensity", "balanced")

# ---- Step 1: Validate video ----
if not os.path.exists(VIDEO):
    raise FileNotFoundError(f"Video file not found: {VIDEO}")

video_size_mb = os.path.getsize(VIDEO) / (1024 * 1024)
print(f"📹 Motivation video file found: {VIDEO} ({video_size_mb:.2f} MB)")
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
            print(f"🎬 Final motivation video renamed to: {video_output_path}")
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
    
    # ✅ Explicitly refresh token before use
    if creds.expired and creds.refresh_token:
        print("🔄 Refreshing authentication token...")
        creds.refresh(Request())
    
    youtube = build("youtube", "v3", credentials=creds, cache_discovery=False)
    print("✅ YouTube API authenticated")
except Exception as e:
    print(f"❌ Authentication failed: {e}")
    raise

# ---- Step 4: 💪 Prepare 5AM LEGION-OPTIMIZED metadata ----
# Enhanced description with motivation-specific CTAs and keywords
enhanced_description = f"""{description}

{' '.join(hashtags)}

💪 {CHANNEL_TAGLINE}

---
⏰ New motivation daily!
🔥 Wake up early. Build discipline. Transform your life.
🎯 Follow {CHANNEL_NAME} for daily motivation & life hacks
🚀 Topics: 5AM Routine • Discipline • Success Mindset • Grindset • Personal Growth

Follow The 5AM Legion:
YouTube   : @The5AMLegion
Instagram : @The5AMLegion
TikTok    : @The5AMLegion
Facebook  : The 5AM Legion

Intensity Level: {intensity.title()}
Created: {datetime.now().strftime('%Y-%m-%d')}
Category: Motivation & Self-Improvement
"""

# 💪 5AM LEGION-SPECIFIC TAGS (optimized for discovery)
motivation_base_tags = [
    "motivation",
    "5am club",
    "discipline",
    "grindset",
    "success",
    "personal growth",
    "mindset",
    "self-improvement",
    "productivity",
    "early morning",
    "morning routine",
    "goal setting",
    "motivation shorts",
    "inspirational",
    "life hacks"
]

# Intensity-specific tags
intensity_tags = {
    'aggressive': ["aggressive motivation", "no excuses", "beast mode", "conquer", "dominate"],
    'balanced': ["consistency", "build habits", "steady growth", "discipline", "progress"],
    'inspirational': ["inspire", "dream big", "believe", "rise above", "transformation"]
}

# Combine base tags with intensity-specific tags
tags = motivation_base_tags.copy()
if intensity in intensity_tags:
    tags.extend(intensity_tags[intensity][:5])

# Add hashtags from script
if hashtags:
    tags.extend([tag.replace('#', '').lower() for tag in hashtags[:10]])

# Add generic viral tags
tags.extend(["shorts", "viral"])

# Remove duplicates and limit to 15 tags (YouTube best practice)
tags = list(dict.fromkeys(tags))[:15]

print(f"📝 Motivation metadata ready:")
print(f"   Title: {title}")
print(f"   Channel: {CHANNEL_NAME}")
print(f"   Intensity: {intensity.title()}")
print(f"   Tags: {', '.join(tags[:10])}...")
print(f"   Hashtags: {' '.join(hashtags[:5])}...")

snippet = {
    "title": title[:100],  # YouTube limit
    "description": enhanced_description[:5000],  # YouTube limit
    "tags": tags,
    "categoryId": "22"  # 💪 Category 22 = "People & Blogs" (best for motivation/lifestyle)
}

body = {
    "snippet": snippet,
    "status": {
        "privacyStatus": "public",
        "selfDeclaredMadeForKids": False,
        "madeForKids": False
    }
}

print(f"📤 Uploading motivation video to YouTube...")

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=2, min=4, max=60))
def upload_video(youtube_client, video_path, metadata):
    # ✅ INCREASED CHUNK SIZE from 1MB to 10MB for better performance
    media = MediaFileUpload(
        video_path,
        chunksize=10*1024*1024,  # 10MB chunks
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
        try:
            status, response = request.next_chunk()
            if status:
                progress = int(status.progress() * 100)
                if progress != last_progress and progress % 10 == 0:
                    print(f"⏳ Upload progress: {progress}%")
                    last_progress = progress
        except HttpError as e:
            # Retry on server errors
            if e.resp.status in [500, 502, 503, 504]:
                print(f"⚠️ Server error {e.resp.status}, retrying chunk...")
                raise
            else:
                raise
    
    return response

try:
    print("🚀 Starting motivation video upload...")
    result = upload_video(youtube, VIDEO, body)
    video_id = result["id"]
    video_url = f"https://www.youtube.com/watch?v={video_id}"
    shorts_url = f"https://www.youtube.com/shorts/{video_id}"
    
    print(f"✅ Motivation video uploaded successfully!")
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
    import traceback
    traceback.print_exc()
    raise

# ---- Step 6: Set thumbnail (desktop view) ----
if os.path.exists(THUMB):
    try:
        print("🖼️ Setting motivation thumbnail for desktop views...")
        thumb_size_mb = os.path.getsize(THUMB) / (1024*1024)
        if thumb_size_mb > 2:
            print(f"⚠️ Compressing thumbnail ({thumb_size_mb:.2f}MB)...")
            img = Image.open(THUMB)
            # 💪 Optimize thumbnail with excellent quality for bold imagery
            img.save(THUMB, quality=92, optimize=True)
        
        youtube.thumbnails().set(
            videoId=video_id, 
            media_body=MediaFileUpload(THUMB)
        ).execute()
        print("✅ Motivation thumbnail set successfully (desktop view).")
    except Exception as e:
        print(f"⚠️ Thumbnail upload failed: {e}")
else:
    print("⚠️ No thumbnail file found, skipping thumbnail set.")

# ---- Step 7: 💪 Save upload history with motivation analytics ----
upload_metadata = {
    "video_id": video_id,
    "title": title,
    "topic": topic,
    "intensity": intensity,
    "channel": CHANNEL_NAME,
    "upload_date": datetime.now().isoformat(),
    "video_url": video_url,
    "shorts_url": shorts_url,
    "hashtags": hashtags,
    "file_size_mb": round(video_size_mb, 2),
    "tags": tags,
    "category": "Motivation & Self-Improvement",
    "content_type": "motivation_short",
    "estimated_duration": data.get("estimated_duration", 0),
    "word_count": data.get("word_count", 0)
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

# 💪 Analytics summary
total_uploads = len(history)
intensity_counts = {}
for h in history:
    intens = h.get('intensity', 'balanced')
    intensity_counts[intens] = intensity_counts.get(intens, 0) + 1

print(f"\n📊 Channel Stats: {total_uploads} motivation videos uploaded total")
if intensity_counts:
    print(f"📈 Motivation Intensity Distribution:")
    for intens, count in sorted(intensity_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"   {intens.title()}: {count} videos")

print("\n" + "="*70)
print("🎉 MOTIVATION VIDEO UPLOAD COMPLETE!")
print("="*70)
print(f"💪 Channel: {CHANNEL_NAME}")
print(f"📹 Title: {title}")
print(f"🏷️  Topic: {topic}")
print(f"⚡ Intensity: {intensity.title()}")
print(f"🆔 Video ID: {video_id}")
print(f"🔗 Shorts URL: {shorts_url}")
print(f"#️⃣  Hashtags: {' '.join(hashtags[:5])}")
print(f"🏷️  Tags: {', '.join(tags[:8])}...")
print("="*70)
print("\n💡 5AM Legion Channel Best Practices:")
print("   • Best posting time: 5-6 AM (early risers) or 8-9 PM (night planners)")
print("   • Peak season: January (New Year resolutions), September (New Goals)")
print("   • Peak days: Monday (motivation spike), Sunday (week prep)")
print("   • Engage with comments within 1 hour for maximum algorithm boost")
print("   • Pin a comment asking 'What's your morning routine?' for engagement")
print("   • Cross-post to TikTok 30 minutes after YouTube for consistency")
print("   • Create playlists by intensity level for better watch time")
print("   • Use end screens to link related motivation content")
print(f"\n🔗 Share this URL: {shorts_url}")
print("💪 Rise early. Dominate the day. 🚀")