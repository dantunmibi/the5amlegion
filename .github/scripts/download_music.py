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

TMP = os.getenv("GITHUB_WORKSPACE", ".") + "/tmp"
MUSIC_DIR = os.path.join(TMP, "music")
os.makedirs(MUSIC_DIR, exist_ok=True)

# 🎵 COPYRIGHT-FREE MUSIC LIBRARY
# Sources: Pixabay Music (CC0 licensed)

MUSIC_LIBRARY = {
    # 🌑 DARK ATMOSPHERIC (Pain/Contemplation)
    'dark_atmospheric': {
        'name': 'Dark Atmospheric Piano',
        'url': 'https://cdn.pixabay.com/download/audio/2022/03/10/audio_0ac3f7621f.mp3',
        'duration': 120,
        'emotion': 'dark, contemplative, tension',
        'scenes': ['pain', 'late_night'],
        'volume_default': 0.12
    },
    
    'ambient_tension': {
        'name': 'Ambient Tension',
        'url': 'https://cdn.pixabay.com/download/audio/2022/05/27/audio_1808fbf07a.mp3',
        'duration': 90,
        'emotion': 'mysterious, building tension',
        'scenes': ['pain'],
        'volume_default': 0.10
    },
    
    # 🔥 BUILDING DRUMS (Wake-up/Urgency)
    'epic_drums': {
        'name': 'Epic Drums Build',
        'url': 'https://cdn.pixabay.com/download/audio/2022/03/15/audio_c8c5229bcf.mp3',
        'duration': 100,
        'emotion': 'building, urgent, powerful',
        'scenes': ['wake_up', 'midday'],
        'volume_default': 0.20
    },
    
    'percussion_rise': {
        'name': 'Percussion Rising',
        'url': 'https://cdn.pixabay.com/download/audio/2023/02/28/audio_02f6a5b3f1.mp3',
        'duration': 85,
        'emotion': 'intense, driving, momentum',
        'scenes': ['wake_up'],
        'volume_default': 0.22
    },
    
    # 🏔️ EPIC ORCHESTRAL (Transformation/Journey)
    'epic_orchestral': {
        'name': 'Epic Orchestral Cinematic',
        'url': 'https://cdn.pixabay.com/download/audio/2022/03/24/audio_4db1103d11.mp3',
        'duration': 130,
        'emotion': 'epic, inspiring, victorious',
        'scenes': ['transformation', 'success'],
        'volume_default': 0.28
    },
    
    'cinematic_inspiration': {
        'name': 'Cinematic Inspiration',
        'url': 'https://cdn.pixabay.com/download/audio/2021/08/04/audio_0625c1539c.mp3',
        'duration': 95,
        'emotion': 'uplifting, powerful, breakthrough',
        'scenes': ['transformation'],
        'volume_default': 0.26
    },
    
    # ⚔️ POWERFUL ACTION (Command/CTA)
    'powerful_action': {
        'name': 'Powerful Action Theme',
        'url': 'https://cdn.pixabay.com/download/audio/2022/06/03/audio_7a87dff2da.mp3',
        'duration': 110,
        'emotion': 'commanding, strong, decisive',
        'scenes': ['action', 'discipline'],
        'volume_default': 0.25
    },
    
    'heroic_resolve': {
        'name': 'Heroic Resolve',
        'url': 'https://cdn.pixabay.com/download/audio/2023/01/12/audio_24b5080dc1.mp3',
        'duration': 88,
        'emotion': 'triumphant, resolving, victorious',
        'scenes': ['action'],
        'volume_default': 0.24
    },
    
    # 🎼 GENERAL EPIC (All-purpose)
    'epic_cinematic': {
        'name': 'Epic Cinematic Motivational',
        'url': 'https://cdn.pixabay.com/download/audio/2022/11/09/audio_1f07dcb1c2.mp3',
        'duration': 140,
        'emotion': 'epic, motivational, building',
        'scenes': ['general', 'morning_fire'],
        'volume_default': 0.20
    },
    
    'inspiring_dramatic': {
        'name': 'Inspiring Dramatic',
        'url': 'https://cdn.pixabay.com/download/audio/2022/09/14/audio_e8ef013c50.mp3',
        'duration': 105,
        'emotion': 'dramatic, inspiring, emotional',
        'scenes': ['general', 'evening'],
        'volume_default': 0.22
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
        response = requests.get(track_info['url'], timeout=60, stream=True)
        
        if response.status_code == 200:
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            # Verify file
            if os.path.exists(filepath) and os.path.getsize(filepath) > 10000:
                print(f"   ✅ Downloaded {os.path.getsize(filepath) / 1024:.1f} KB")
                
                # Update cache
                cache[track_key] = {
                    'name': track_info['name'],
                    'local_path': filepath,
                    'url': track_info['url'],
                    'duration': track_info['duration'],
                    'emotion': track_info['emotion'],
                    'scenes': track_info['scenes'],
                    'volume_default': track_info['volume_default'],
                    'downloaded_at': os.popen('date -u +%Y-%m-%dT%H:%M:%SZ').read().strip()
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
    
    print("\n" + "="*70)
    print("📊 DOWNLOAD SUMMARY")
    print("="*70)
    print(f"✅ Successful: {successful}/{total}")
    print(f"❌ Failed: {len(failed)}/{total}")
    
    if failed:
        print(f"\nFailed tracks: {', '.join(failed)}")
    
    print(f"\n💾 Music library location: {MUSIC_DIR}")
    
    return successful, failed


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
        
    else:
        print("🎵 Music Download Utility")
        print("\nUsage:")
        print("  python download_music.py --download-all  # Download all tracks")
        print("  python download_music.py --cleanup       # Remove old tracks")
        print("  python download_music.py --list          # List library")
        print("\nDownloading essential tracks...")
        
        # Download one track from each category
        essential = ['dark_atmospheric', 'epic_drums', 'epic_orchestral', 'powerful_action']
        
        for track_key in essential:
            if track_key in MUSIC_LIBRARY:
                download_track(track_key, MUSIC_LIBRARY[track_key])
        
        print("\n✅ Essential tracks ready")