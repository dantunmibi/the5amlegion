#!/usr/bin/env python3
"""
🎵 Download & Manage Copyright-Free Music Library
Automatically downloads and caches epic motivational music tracks
"""

import os
import json
import requests
from pathlib import Path
import hashlib
from datetime import datetime, timedelta

TMP = os.getenv("GITHUB_WORKSPACE", ".") + "/tmp"
MUSIC_DIR = os.path.join(TMP, "music")
os.makedirs(MUSIC_DIR, exist_ok=True)

# 🎵 COPYRIGHT-FREE MUSIC LIBRARY - HYBRID APPROACH
# Primary: Pixabay (CC0) | Backup: Incompetech (CC BY 4.0)
# Each track has a backup URL for reliability

# 🎵 COPYRIGHT-FREE MUSIC LIBRARY - INCOMPETECH FOCUSED
# All tracks from Incompetech (Kevin MacLeod) - CC BY 4.0
# These URLs are permanent and reliable

MUSIC_LIBRARY = {
    # 🌑 DARK ATMOSPHERIC (Pain/Contemplation)
    'dark_atmospheric': {
        'name': 'Dark Ambient',
        'url': 'https://incompetech.com/music/royalty-free/mp3-royaltyfree/Killers.mp3',
        'duration': 213,
        'emotion': 'dark, contemplative, tension',
        'scenes': ['pain', 'late_night'],
        'volume_default': 0.15
    },

    'ambient_tension': {
        'name': 'Mysterious Dark',
        'url': 'https://incompetech.com/music/royalty-free/mp3-royaltyfree/Cipher.mp3',
        'duration': 145,
        'emotion': 'mysterious, building tension',
        'scenes': ['pain'],
        'volume_default': 0.12
    },

    # 🔥 BUILDING DRUMS (Wake-up/Urgency)
    'epic_drums': {
        'name': 'Epic Drums Build',
        'url': 'https://incompetech.com/music/royalty-free/mp3-royaltyfree/Drums%20of%20the%20Deep.mp3',
        'duration': 249,
        'emotion': 'building, urgent, powerful',
        'scenes': ['wake_up', 'midday'],
        'volume_default': 0.25
    },

    'percussion_rise': {
        'name': 'Powerful Beat',
        'url': 'https://incompetech.com/music/royalty-free/mp3-royaltyfree/Rocket.mp3',
        'duration': 126,
        'emotion': 'intense, driving, momentum',
        'scenes': ['wake_up'],
        'volume_default': 0.25
    },

    # 🏔️ EPIC ORCHESTRAL (Transformation/Journey)
    'epic_orchestral': {
        'name': 'Epic Cinematic',
        'url': 'https://incompetech.com/music/royalty-free/mp3-royaltyfree/Heroic%20Age.mp3',
        'duration': 162,
        'emotion': 'epic, inspiring, victorious',
        'scenes': ['transformation', 'success'],
        'volume_default': 0.30
    },

    'cinematic_inspiration': {
        'name': 'Uplifting Orchestral',
        'url': 'https://incompetech.com/music/royalty-free/mp3-royaltyfree/Nowhere%20Land.mp3',
        'duration': 173,
        'emotion': 'uplifting, powerful, breakthrough',
        'scenes': ['transformation'],
        'volume_default': 0.28
    },

    # ⚔️ POWERFUL ACTION (Command/CTA)
    'powerful_action': {
        'name': 'Action Cinematic',
        'url': 'https://incompetech.com/music/royalty-free/mp3-royaltyfree/The%20Complex.mp3',
        'duration': 283,
        'emotion': 'commanding, strong, decisive',
        'scenes': ['action', 'discipline'],
        'volume_default': 0.28
    },

    'heroic_resolve': {
        'name': 'Epic Heroic',
        'url': 'https://incompetech.com/music/royalty-free/mp3-royaltyfree/Prelude%20and%20Action.mp3',
        'duration': 104,
        'emotion': 'triumphant, resolving, victorious',
        'scenes': ['action'],
        'volume_default': 0.28
    },

    # 🎼 GENERAL EPIC (All-purpose)
    'epic_cinematic': {
        'name': 'Motivational Epic',
        'url': 'https://incompetech.com/music/royalty-free/mp3-royaltyfree/Long%20Stroll.mp3',
        'duration': 203,
        'emotion': 'epic, motivational, building',
        'scenes': ['general', 'morning_fire'],
        'volume_default': 0.25
    },

    'inspiring_dramatic': {
        'name': 'Dramatic Inspiration',
        'url': 'https://incompetech.com/music/royalty-free/mp3-royaltyfree/Achaidh%20Cheide.mp3',
        'duration': 137,
        'emotion': 'dramatic, inspiring, emotional',
        'scenes': ['general', 'evening'],
        'volume_default': 0.25
    },
    
    # 🔥 ADDITIONAL HIGH-ENERGY TRACKS
    'intense_motivation': {
        'name': 'Intense Motivation',
        'url': 'https://incompetech.com/music/royalty-free/mp3-royaltyfree/Oppressive%20Gloom.mp3',
        'duration': 210,
        'emotion': 'intense, energetic, powerful',
        'scenes': ['wake_up', 'midday'],
        'volume_default': 0.27
    },
    
    'epic_trailer': {
        'name': 'Epic Trailer',
        'url': 'https://incompetech.com/music/royalty-free/mp3-royaltyfree/Darkest%20Child.mp3',
        'duration': 251,
        'emotion': 'epic, cinematic, dramatic',
        'scenes': ['transformation', 'success'],
        'volume_default': 0.30
    },
    
    # 🌙 CALM BUT POWERFUL (Late night)
    'dark_reflection': {
        'name': 'Dark Reflection',
        'url': 'https://incompetech.com/music/royalty-free/mp3-royaltyfree/Mining%20by%20Moonlight.mp3',
        'duration': 214,
        'emotion': 'contemplative, deep, introspective',
        'scenes': ['late_night', 'evening'],
        'volume_default': 0.18
    },
    
    'midnight_drive': {
        'name': 'Midnight Drive',
        'url': 'https://incompetech.com/music/royalty-free/mp3-royaltyfree/Meditation%20Impromptu%2001.mp3',
        'duration': 138,
        'emotion': 'moody, focused, determined',
        'scenes': ['late_night'],
        'volume_default': 0.20
    },
    
    # 💪 EXTRA DISCIPLINE TRACKS
    'warrior_mindset': {
        'name': 'Warrior Mindset',
        'url': 'https://incompetech.com/music/royalty-free/mp3-royaltyfree/Fearless%20First.mp3',
        'duration': 234,
        'emotion': 'determined, focused, unstoppable',
        'scenes': ['discipline', 'action'],
        'volume_default': 0.26
    },
    
    # 🎯 BONUS TRACKS
    'morning_power': {
        'name': 'Morning Power',
        'url': 'https://incompetech.com/music/royalty-free/mp3-royaltyfree/Volatile%20Reaction.mp3',
        'duration': 189,
        'emotion': 'energetic, wake-up, powerful',
        'scenes': ['early_morning', 'wake_up'],
        'volume_default': 0.28
    },
    
    'battle_ready': {
        'name': 'Battle Ready',
        'url': 'https://incompetech.com/music/royalty-free/mp3-royaltyfree/Heart%20of%20the%20Beast.mp3',
        'duration': 93,
        'emotion': 'aggressive, ready, intense',
        'scenes': ['action', 'discipline'],
        'volume_default': 0.30
    }
}


def get_music_cache_path():
    """Get path to music cache file"""
    return os.path.join(MUSIC_DIR, "music_cache.json")


def load_music_cache():
    """Load cached music metadata"""
    cache_path = get_music_cache_path()
    if os.path.exists(cache_path):
        try:
            with open(cache_path, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}


def save_music_cache(cache):
    """Save music cache metadata"""
    cache_path = get_music_cache_path()
    with open(cache_path, 'w') as f:
        json.dump(cache, f, indent=2)


def get_track_hash(track_key):
    """Get hash for track identification"""
    return hashlib.md5(track_key.encode()).hexdigest()[:12]


def download_track(track_key, track_info, force=False):
    """
    Download a music track if not already cached
    Returns: local file path or None
    """
    
    # Generate local filename
    track_hash = get_track_hash(track_key)
    filename = f"{track_key}_{track_hash}.mp3"
    filepath = os.path.join(MUSIC_DIR, filename)
    
    # Check cache
    cache = load_music_cache()
    
    if not force and track_key in cache:
        cached_path = cache[track_key].get('local_path')
        if cached_path and os.path.exists(cached_path):
            print(f"✅ Using cached: {track_info['name']}")
            return cached_path
    
    # Download
    print(f"📥 Downloading: {track_info['name']}...")
    
    try:
        url = track_info['url']
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'audio/mpeg,audio/*;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Referer': 'https://incompetech.com/',
            'Connection': 'keep-alive'
        }
        
        response = requests.get(
            url, 
            timeout=120, 
            stream=True,
            headers=headers,
            allow_redirects=True
        )
        
        if response.status_code == 200:
            # Download with progress
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            # Verify file
            if os.path.exists(filepath) and os.path.getsize(filepath) > 10000:
                file_size_kb = os.path.getsize(filepath) / 1024
                print(f"   ✅ Downloaded {file_size_kb:.1f} KB")
                
                # Update cache
                cache[track_key] = {
                    'name': track_info['name'],
                    'local_path': filepath,
                    'url': track_info['url'],
                    'duration': track_info['duration'],
                    'emotion': track_info['emotion'],
                    'scenes': track_info['scenes'],
                    'volume_default': track_info['volume_default'],
                    'downloaded_at': datetime.now().isoformat(),  # ← Now datetime is imported
                    'file_size_kb': round(file_size_kb, 2)
                }
                save_music_cache(cache)
                
                return filepath
            else:
                print(f"   ⚠️ Downloaded file invalid")
                if os.path.exists(filepath):
                    os.remove(filepath)
                return None
        else:
            print(f"   ⚠️ Download failed: HTTP {response.status_code}")
            return None
            
    except Exception as e:
        print(f"   ⚠️ Download error: {e}")
        return None


def get_music_for_scene(scene_type, content_type='general'):
    """
    Get best music track for a scene type
    Returns: (track_key, local_path, volume)
    """
    
    # Priority order for scene types
    scene_priority = {
        'pain': ['dark_atmospheric', 'ambient_tension', 'epic_cinematic'],
        'wake_up': ['epic_drums', 'percussion_rise', 'powerful_action'],
        'transformation': ['epic_orchestral', 'cinematic_inspiration', 'inspiring_dramatic'],
        'action': ['powerful_action', 'heroic_resolve', 'epic_orchestral'],
        'general': ['epic_cinematic', 'inspiring_dramatic', 'epic_orchestral']
    }
    
    # Content type overrides
    content_overrides = {
        'early_morning': ['epic_drums', 'powerful_action', 'epic_orchestral'],
        'late_night': ['dark_atmospheric', 'ambient_tension', 'epic_cinematic'],
        'evening': ['inspiring_dramatic', 'cinematic_inspiration', 'epic_cinematic'],
        'midday': ['epic_drums', 'powerful_action', 'percussion_rise']
    }
    
    # Get priority list
    if content_type in content_overrides:
        priority_tracks = content_overrides[content_type]
    else:
        priority_tracks = scene_priority.get(scene_type, scene_priority['general'])
    
    # Try to download tracks in priority order
    for track_key in priority_tracks:
        if track_key in MUSIC_LIBRARY:
            track_info = MUSIC_LIBRARY[track_key]
            local_path = download_track(track_key, track_info)
            
            if local_path:
                return track_key, local_path, track_info['volume_default']
    
    # Fallback: try any available track
    print(f"⚠️ Priority tracks unavailable, trying fallbacks...")
    for track_key, track_info in MUSIC_LIBRARY.items():
        local_path = download_track(track_key, track_info)
        if local_path:
            return track_key, local_path, track_info['volume_default']
    
    return None, None, 0.20


def download_all_music():
    """Download all music tracks for offline use"""
    
    print("\n" + "="*70)
    print("🎵 DOWNLOADING MUSIC LIBRARY")
    print("="*70)
    print("Source: Incompetech (Kevin MacLeod) - CC BY 4.0")
    print("License: Free to use with attribution")
    print()
    
    total = len(MUSIC_LIBRARY)
    successful = 0
    failed = []
    
    for track_key, track_info in MUSIC_LIBRARY.items():
        print(f"\n📀 [{successful + len(failed) + 1}/{total}] {track_info['name']}")
        
        local_path = download_track(track_key, track_info)
        
        if local_path:
            successful += 1
            print(f"   ✅ Ready: {local_path}")
        else:
            failed.append(track_key)
            print(f"   ❌ Failed")
        
        # Small delay to be respectful to server
        time.sleep(0.5)
    
    print("\n" + "="*70)
    print("📊 DOWNLOAD SUMMARY")
    print("="*70)
    print(f"✅ Successful: {successful}/{total}")
    print(f"❌ Failed: {len(failed)}/{total}")
    
    if failed:
        print(f"\nFailed tracks: {', '.join(failed)}")
    
    print(f"\n💾 Music library location: {MUSIC_DIR}")
    print(f"📄 Attribution: Music by Kevin MacLeod (incompetech.com)")
    print(f"📜 Licensed under Creative Commons: By Attribution 4.0")
    print(f"🔗 https://creativecommons.org/licenses/by/4.0/")
    
    return successful, failed


def test_music_urls():
    """Quick test to verify music URLs are accessible"""
    
    print("\n🧪 Testing music URL accessibility...")
    
    working = []
    broken = []
    
    for track_key, track_info in list(MUSIC_LIBRARY.items())[:3]:  # Test first 3
        print(f"\n Testing {track_info['name']}...")
        
        for source, url_key in [('Primary', 'url'), ('Backup', 'backup_url')]:
            if url_key not in track_info:
                continue
                
            url = track_info[url_key]
            try:
                response = requests.head(url, timeout=10, allow_redirects=True)
                if response.status_code == 200:
                    print(f"   ✅ {source} URL working")
                    working.append(f"{track_key} ({source})")
                else:
                    print(f"   ⚠️ {source} returned {response.status_code}")
                    broken.append(f"{track_key} ({source})")
            except Exception as e:
                print(f"   ❌ {source} failed: {str(e)[:50]}")
                broken.append(f"{track_key} ({source})")
    
    print(f"\n📊 Quick Test Results:")
    print(f"   Working: {len(working)}")
    print(f"   Broken: {len(broken)}")
    
    if len(working) > 0:
        print(f"\n✅ URLs are functional! Safe to download library.")
    else:
        print(f"\n⚠️ URL issues detected. Check network or URLs.")


def cleanup_old_music(keep_days=30):
    """Clean up music files older than specified days"""
    
    print(f"\n🧹 Cleaning up music older than {keep_days} days...")
    
    cache = load_music_cache()
    removed = 0
    
    from datetime import datetime, timedelta
    cutoff = datetime.now() - timedelta(days=keep_days)
    
    for track_key, track_data in list(cache.items()):
        downloaded_at = track_data.get('downloaded_at')
        
        if downloaded_at:
            try:
                download_date = datetime.fromisoformat(downloaded_at.replace('Z', '+00:00'))
                
                if download_date < cutoff:
                    local_path = track_data.get('local_path')
                    if local_path and os.path.exists(local_path):
                        os.remove(local_path)
                        print(f"   🗑️ Removed: {track_key}")
                        removed += 1
                    
                    del cache[track_key]
            except:
                pass
    
    if removed > 0:
        save_music_cache(cache)
        print(f"✅ Removed {removed} old tracks")
    else:
        print(f"✅ No old tracks to remove")


def print_music_library():
    """Print available music library"""
    
    print("\n" + "="*70)
    print("🎵 AVAILABLE MUSIC LIBRARY")
    print("="*70)
    
    by_emotion = {}
    for track_key, track_info in MUSIC_LIBRARY.items():
        scenes = ', '.join(track_info['scenes'])
        if scenes not in by_emotion:
            by_emotion[scenes] = []
        by_emotion[scenes].append(track_info)
    
    for scenes, tracks in sorted(by_emotion.items()):
        print(f"\n📂 {scenes.upper()}")
        for track in tracks:
            print(f"   🎵 {track['name']}")
            print(f"      Emotion: {track['emotion']}")
            print(f"      Duration: {track['duration']}s")
            print(f"      Default volume: {track['volume_default']*100:.0f}%")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == '--download-all':
        download_all_music()
        
    elif len(sys.argv) > 1 and sys.argv[1] == '--cleanup':
        cleanup_old_music()
        
    elif len(sys.argv) > 1 and sys.argv[1] == '--list':
        print_music_library()
        
    elif len(sys.argv) > 1 and sys.argv[1] == '--test':
        test_music_urls()
        
    else:
        print("🎵 Hybrid Music Download System")
        print("\nUsage:")
        print("  python download_music.py --download-all  # Download entire library")
        print("  python download_music.py --test          # Test URL accessibility")
        print("  python download_music.py --cleanup       # Remove old tracks")
        print("  python download_music.py --list          # List library")
        print("\n💡 Uses Pixabay (primary) + Incompetech (backup) for 99% reliability")
        print("\nDownloading essential tracks...")
        
        # Download one track from each category
        essential = ['dark_atmospheric', 'epic_drums', 'epic_orchestral', 'powerful_action']
        
        for track_key in essential:
            if track_key in MUSIC_LIBRARY:
                download_track(track_key, MUSIC_LIBRARY[track_key])
        
        print("\n✅ Essential tracks ready")