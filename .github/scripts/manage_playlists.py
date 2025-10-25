#!/usr/bin/env python3
"""
🔥 Manage Motivational Playlists - ROBUST VERSION
Organizes videos into content pillars:
- Morning Fire (30%)
- Discipline & Grind (25%)
- Mindset Shifts (20%)
- Late Night Accountability (15%)
- Success Stories (10%)
"""

import os
import json
from datetime import datetime
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.oauth2.credentials import Credentials
from collections import defaultdict
import re
import difflib
import time

TMP = os.getenv("GITHUB_WORKSPACE", ".") + "/tmp"
PLAYLIST_CONFIG_FILE = os.path.join(TMP, "playlist_config.json")
UPLOAD_LOG = os.path.join(TMP, "upload_history.json")


def get_youtube_client():
    """Authenticate YouTube API"""
    try:
        creds = Credentials(
            None,
            refresh_token=os.getenv("GOOGLE_REFRESH_TOKEN"),
            token_uri="https://oauth2.googleapis.com/token",
            client_id=os.getenv("GOOGLE_CLIENT_ID"),
            client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
            scopes=["https://www.googleapis.com/auth/youtube"]
        )
        youtube = build("youtube", "v3", credentials=creds, cache_discovery=False)
        print("✅ YouTube API authenticated")
        return youtube
    except Exception as e:
        print(f"❌ Authentication failed: {e}")
        raise


# 🔥 MOTIVATION PLAYLIST CONFIGURATION
PLAYLIST_RULES = {
    "motivation": {
        "morning_fire": {
            "title": "🔥 Morning Fire - 5 AM Warriors",
            "description": "Aggressive wake-up calls for champions. Start your day with intensity. No snooze, no excuses. Join the 5 AM Legion.",
            "keywords": [
                "5 am", "5am", "morning", "wake up", "early", "sunrise", "dawn",
                "morning routine", "morning motivation", "start your day", "wake up early",
                "first hour", "morning grind", "before work", "breakfast motivation",
                "early riser", "morning warrior", "5 am club", "morning discipline",
                "get up", "alarm", "snooze", "bed", "sleep", "tired", "exhausted"
            ]
        },
        "discipline": {
            "title": "💪 Discipline & Grind - No Days Off",
            "description": "Hard work, relentless effort, no shortcuts. The grind never stops. Discipline beats motivation every time.",
            "keywords": [
                "discipline", "grind", "hustle", "work hard", "no days off", "relentless",
                "hard work", "effort", "consistency", "daily", "every day", "no excuses",
                "push through", "keep going", "don't quit", "never give up", "persist",
                "dedication", "commitment", "focus", "grind mode", "beast mode",
                "work ethic", "sacrifice", "tough", "strong", "warrior", "champion",
                "training", "gym", "workout", "fitness", "athlete", "performance"
            ]
        },
        "mindset": {
            "title": "🧠 Mindset Shifts - Mental Toughness",
            "description": "Change how you think, change your life. Reframe failure, build mental toughness, think like winners.",
            "keywords": [
                "mindset", "mental", "think", "believe", "thoughts", "psychology",
                "mental toughness", "resilience", "overcome", "adversity", "challenge",
                "growth mindset", "fixed mindset", "limiting beliefs", "self doubt",
                "confidence", "self belief", "faith", "trust", "vision", "perspective",
                "reframe", "shift", "change", "transformation", "evolve", "adapt",
                "failure", "setback", "obstacle", "problem", "solution", "breakthrough",
                "fear", "anxiety", "stress", "pressure", "cope", "handle", "manage"
            ]
        },
        "late_night": {
            "title": "🌙 Late Night Truth - 2 AM Accountability",
            "description": "For those scrolling at 2 AM. Honest conversations about wasted time and tomorrow's potential. Set your alarm now.",
            "keywords": [
                "2 am", "2am", "late night", "midnight", "can't sleep", "insomnia",
                "scrolling", "phone", "bed", "awake", "night", "evening", "darkness",
                "guilt", "regret", "wasted time", "procrastination", "tomorrow",
                "accountability", "honest", "truth", "reality", "wake up call",
                "existential", "crisis", "question", "doubt", "worry", "anxiety",
                "reflection", "introspection", "think", "alone", "solitude",
                "future self", "potential", "wasting", "stuck", "lost", "direction"
            ]
        },
        "success": {
            "title": "🏆 Success Stories - Proof It's Possible",
            "description": "Real transformation stories. From zero to hero. They did it, you can too. Inspiration backed by proof.",
            "keywords": [
                "success", "transformation", "before after", "journey", "story",
                "achievement", "accomplish", "goal", "dream", "win", "victory",
                "champion", "winner", "best", "top", "elite", "pro", "master",
                "from broke to", "rags to riches", "comeback", "rise", "climb",
                "zero to hero", "underdog", "overcome", "beat the odds", "prove them wrong",
                "made it", "successful", "millionaire", "rich", "wealth", "money",
                "business", "entrepreneur", "startup", "company", "empire", "build"
            ]
        }
    }
}


def fetch_and_map_existing_playlists(youtube, niche, config):
    """Fetch existing playlists and map to categories"""
    print("🔄 Fetching existing playlists...")
    existing_playlists = {}
    nextPageToken = None
    
    while True:
        response = youtube.playlists().list(
            part="snippet",
            mine=True,
            maxResults=50,
            pageToken=nextPageToken
        ).execute()
        
        for item in response.get("items", []):
            existing_playlists[item["snippet"]["title"].lower()] = item["id"]
        
        nextPageToken = response.get("nextPageToken")
        if not nextPageToken:
            break
    
    # Map to categories using fuzzy matching
    for category, rules in PLAYLIST_RULES[niche].items():
        key = f"{niche}_{category}"
        match = None
        
        for title, pid in existing_playlists.items():
            ratio = difflib.SequenceMatcher(None, rules["title"].lower(), title).ratio()
            if ratio > 0.6:
                match = pid
                break
        
        if match:
            if key in config and config[key] != match:
                print(f"♻️ Updated playlist ID for '{rules['title']}'")
            else:
                print(f"✅ Mapped '{rules['title']}'")
            config[key] = match
    
    return config


def load_upload_history():
    """Load video upload history"""
    if os.path.exists(UPLOAD_LOG):
        try:
            with open(UPLOAD_LOG, 'r') as f:
                return json.load(f)
        except:
            return []
    return []


def load_playlist_config():
    """Load playlist configuration"""
    if os.path.exists(PLAYLIST_CONFIG_FILE):
        try:
            with open(PLAYLIST_CONFIG_FILE, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}


def save_playlist_config(config):
    """Save playlist configuration"""
    with open(PLAYLIST_CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)
    print(f"💾 Saved playlist config: {len(config)} playlists")


def get_or_create_playlist(youtube, niche, category, config):
    """Get existing playlist or create new one"""
    playlist_key = f"{niche}_{category}"
    
    if playlist_key in config:
        print(f"✅ Using existing playlist: {playlist_key}")
        return config[playlist_key]
    
    # Create new playlist
    try:
        playlist_info = PLAYLIST_RULES[niche][category]
        title = playlist_info["title"]
        description = playlist_info["description"]
        
        # Add branding
        full_description = f"{description}\n\n🔥 The 5 AM Legion - Daily motivation for warriors who refuse to quit.\nJoin the movement. #discipline #motivation #5am"
        
        request = youtube.playlists().insert(
            part="snippet,status",
            body={
                "snippet": {
                    "title": title,
                    "description": full_description,
                },
                "status": {"privacyStatus": "public"}
            }
        )
        response = request.execute()
        playlist_id = response["id"]
        
        config[playlist_key] = playlist_id
        save_playlist_config(config)
        print(f"🎉 Created playlist: {title}")
        return playlist_id
        
    except Exception as e:
        print(f"❌ Failed to create playlist: {e}")
        return None


def categorize_video(video_metadata, niche):
    """Smart categorization using keyword matching"""
    text = " ".join([
        video_metadata.get("title", ""),
        video_metadata.get("description", ""),
        video_metadata.get("hook", ""),
        video_metadata.get("key_phrase", ""),
        " ".join(video_metadata.get("hashtags", []))
    ]).lower()
    
    if niche not in PLAYLIST_RULES:
        return None
    
    scores = {}
    for category, rules in PLAYLIST_RULES[niche].items():
        score = 0
        
        # Exact keyword matches
        for kw in rules["keywords"]:
            kw_lower = kw.lower()
            if kw_lower in text:
                score += 5
            
            # Partial matches
            for word in kw_lower.split():
                if len(word) > 3 and word in text:
                    score += 2
                else:
                    # Fuzzy matching
                    for text_word in text.split():
                        if len(text_word) > 3:
                            ratio = difflib.SequenceMatcher(None, word, text_word).ratio()
                            if ratio > 0.85:
                                score += 1
        
        # Bonus for power phrases
        power_phrases = {
            "morning_fire": ["wake up", "5 am", "morning routine", "start your day"],
            "discipline": ["hard work", "no excuses", "grind", "discipline"],
            "mindset": ["mental", "mindset", "believe", "think"],
            "late_night": ["2 am", "late night", "can't sleep", "scrolling"],
            "success": ["success", "transformation", "winner", "achieved"]
        }
        
        if category in power_phrases:
            for phrase in power_phrases[category]:
                if phrase in text:
                    score += 3
        
        if score > 0:
            scores[category] = score
    
    if scores:
        best = max(scores, key=scores.get)
        print(f"   📂 Categorized as: {best} (score: {scores[best]})")
        return best
    
    print("   ⚠️ No match, defaulting to 'discipline'")
    return "discipline"


def add_video_to_playlist(youtube, video_id, playlist_id):
    """Add video to playlist with retry logic"""
    
    # Check if already in playlist
    existing_videos = set()
    max_retries = 3
    
    for attempt in range(max_retries):
        try:
            nextPageToken = None
            while True:
                response = youtube.playlistItems().list(
                    part="snippet",
                    playlistId=playlist_id,
                    maxResults=50,
                    pageToken=nextPageToken
                ).execute()
                
                for item in response.get("items", []):
                    existing_videos.add(item["snippet"]["resourceId"]["videoId"])
                
                nextPageToken = response.get("nextPageToken")
                if not nextPageToken:
                    break
            break
            
        except HttpError as e:
            if e.resp.status == 404 and attempt < max_retries - 1:
                wait = 2 ** attempt
                print(f"      ⏳ Playlist not ready, waiting {wait}s...")
                time.sleep(wait)
            else:
                print(f"      ⚠️ Could not check playlist: {e}")
                break
    
    if video_id in existing_videos:
        print("      ℹ️ Already in playlist")
        return False
    
    # Add video
    for attempt in range(max_retries):
        try:
            youtube.playlistItems().insert(
                part="snippet",
                body={
                    "snippet": {
                        "playlistId": playlist_id,
                        "resourceId": {"kind": "youtube#video", "videoId": video_id}
                    }
                }
            ).execute()
            print("      ✅ Added to playlist")
            return True
            
        except HttpError as e:
            if e.resp.status == 404 and attempt < max_retries - 1:
                wait = 2 ** attempt
                print(f"      ⏳ Retrying in {wait}s...")
                time.sleep(wait)
            else:
                print(f"      ❌ Failed: {e}")
                return False
    
    return False


def organize_playlists(youtube, history, config, niche):
    """Main organization function"""
    print(f"\n🎬 Organizing {len(history)} videos into playlists...")
    
    stats = {
        "total_videos": len(history),
        "categorized": 0,
        "added_to_playlists": 0,
        "already_in_playlists": 0,
        "failed": 0
    }
    
    for video in history:
        video_id = video.get("video_id")
        title = video.get("title", "Unknown")
        
        if not video_id:
            continue
        
        print(f"\n📹 Processing: {title}")
        
        # Categorize
        category = categorize_video(video, niche)
        
        if not category:
            stats["failed"] += 1
            continue
        
        stats["categorized"] += 1
        
        # Get/create playlist
        playlist_id = get_or_create_playlist(youtube, niche, category, config)
        
        if not playlist_id:
            stats["failed"] += 1
            continue
        
        # Add to playlist
        success = add_video_to_playlist(youtube, video_id, playlist_id)
        
        if success:
            stats["added_to_playlists"] += 1
        else:
            stats["already_in_playlists"] += 1
    
    return stats


def print_playlist_summary(config, niche):
    """Print summary"""
    print("\n" + "="*70)
    print("🔥 MOTIVATIONAL PLAYLIST SUMMARY")
    print("="*70)
    
    if niche in PLAYLIST_RULES:
        for category, rules in PLAYLIST_RULES[niche].items():
            key = f"{niche}_{category}"
            
            if key in config:
                playlist_id = config[key]
                url = f"https://www.youtube.com/playlist?list={playlist_id}"
                
                print(f"\n{rules['title']}")
                print(f"   📍 Category: {category}")
                print(f"   🔗 URL: {url}")
                print(f"   📝 {rules['description'][:80]}...")
            else:
                print(f"\n⚠️ {rules['title']}")
                print(f"   Status: Will be auto-created")


if __name__ == "__main__":
    print("🔥 The 5 AM Legion - YouTube Playlist Auto-Organizer")
    print("="*70)
    
    niche = "motivation"
    print(f"🎯 Channel Niche: {niche}")
    
    # Load data
    history = load_upload_history()
    config = load_playlist_config()
    
    if not history:
        print("⚠️ No upload history. Upload videos first!")
        exit(0)
    
    print(f"📂 Found {len(history)} videos")
    
    # Authenticate
    youtube = get_youtube_client()
    
    # Map existing playlists
    config = fetch_and_map_existing_playlists(youtube, niche, config)
    save_playlist_config(config)
    
    # Organize
    stats = organize_playlists(youtube, history, config, niche)
    
    # Results
    print("\n" + "="*70)
    print("📊 ORGANIZATION RESULTS")
    print("="*70)
    print(f"🔥 Total videos: {stats['total_videos']}")
    print(f"✅ Categorized: {stats['categorized']}")
    print(f"📥 Added: {stats['added_to_playlists']}")
    print(f"📋 Already in playlists: {stats['already_in_playlists']}")
    print(f"❌ Failed: {stats['failed']}")
    
    # Summary
    print_playlist_summary(config, niche)
    
    print("\n✅ Playlist organization complete! 🔥")
    print("\n💡 Your playlists will automatically grow with each upload!")
    print("   This maximizes watch time and viewer retention! 💪")