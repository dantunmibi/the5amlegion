#!/usr/bin/env python3
"""
Upload video to Cloudinary for Make.com webhook access
With fallback: use platform URLs if Cloudinary fails
"""

import os
import sys
import json

def upload_video_for_makecom(video_path):
    """
    Upload video to Cloudinary with graceful fallback
    Returns: video URL or None
    """
    
    # Check if Cloudinary is configured
    cloud_name = os.getenv("CLOUDINARY_CLOUD_NAME")
    api_key = os.getenv("CLOUDINARY_API_KEY")
    api_secret = os.getenv("CLOUDINARY_API_SECRET")
    
    if not all([cloud_name, api_key, api_secret]):
        print("⚠️ Cloudinary not configured (optional)")
        print("   Make.com webhook will use platform URLs instead")
        return None
    
    try:
        import cloudinary
        import cloudinary.uploader
        
        # Configure
        cloudinary.config(
            cloud_name=cloud_name,
            api_key=api_key,
            api_secret=api_secret,
            secure=True
        )
        
        print(f"📤 Uploading to Cloudinary...")
        print(f"   Video: {os.path.basename(video_path)}")
        print(f"   Size: {os.path.getsize(video_path) / (1024*1024):.2f} MB")
        
        # Upload
        result = cloudinary.uploader.upload(
            video_path,
            resource_type="video",
            folder="motivation_shorts",
            public_id=f"video_{os.getenv('GITHUB_RUN_NUMBER', 'test')}",
            overwrite=True,
            quality="auto",
            format="mp4"
        )
        
        video_url = result.get("secure_url")
        print(f"✅ Cloudinary upload successful")
        print(f"   URL: {video_url}")
        
        return video_url
        
    except ImportError:
        print("⚠️ Cloudinary library not installed (optional)")
        return None
        
    except Exception as e:
        error_msg = str(e)
        
        # Common Cloudinary errors
        if "cloud_name is disabled" in error_msg:
            print("⚠️ Cloudinary account disabled or expired")
            print("   This is optional - using platform URLs instead")
        elif "Invalid credentials" in error_msg:
            print("⚠️ Cloudinary credentials invalid")
        elif "quota" in error_msg.lower():
            print("⚠️ Cloudinary quota exceeded")
        else:
            print(f"⚠️ Cloudinary upload failed: {error_msg}")
        
        print("   → Make.com will use YouTube/Facebook URLs instead")
        return None


def get_fallback_video_url():
    """
    Get video URL from platform uploads as fallback
    Returns: best available URL
    """
    
    # Try to get platform URLs from multiplatform log
    log_path = "tmp/multiplatform_log.json"
    
    if os.path.exists(log_path):
        try:
            with open(log_path, 'r') as f:
                log = json.load(f)
            
            if log and len(log) > 0:
                latest = log[-1]
                results = latest.get('results', [])
                
                # Priority: YouTube > Facebook > TikTok > Instagram
                for platform in ['youtube', 'facebook', 'tiktok', 'instagram']:
                    for result in results:
                        if result.get('platform') == platform and result.get('url'):
                            url = result['url']
                            print(f"✅ Using {platform.upper()} URL as fallback")
                            print(f"   {url}")
                            return url
        
        except Exception as e:
            print(f"⚠️ Could not read platform URLs: {e}")
    
    # Last resort: GitHub artifacts URL
    repo = os.getenv('GITHUB_REPOSITORY', 'unknown/repo')
    run_id = os.getenv('GITHUB_RUN_ID', '0')
    
    artifacts_url = f"https://github.com/{repo}/actions/runs/{run_id}"
    print(f"⚠️ Using GitHub artifacts URL as fallback")
    print(f"   {artifacts_url}")
    
    return artifacts_url


def main():
    """Main upload function with fallback"""
    
    # Get video path
    video_path = os.getenv("VIDEO_TO_UPLOAD")
    
    if not video_path:
        # Try default locations
        possible_paths = [
            "tmp/short.mp4",
            "tmp/YOURE_NOT_TIRED_YOURE_UNDISCIPLINED_Tonight.mp4"
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                video_path = path
                break
    
    if not video_path or not os.path.exists(video_path):
        print("❌ Video file not found!")
        sys.exit(1)
    
    print(f"✅ Using video: {video_path}")
    
    # Try Cloudinary upload
    video_url = upload_video_for_makecom(video_path)
    
    # Fallback to platform URLs if Cloudinary fails
    if not video_url:
        video_url = get_fallback_video_url()
    
    # Save URL for next step
    os.makedirs("tmp", exist_ok=True)
    
    with open("tmp/video_url.txt", "w") as f:
        f.write(video_url)
    
    print(f"\n✅ Video URL ready for Make.com webhook")
    print(f"   {video_url}")
    
    # Also save metadata
    metadata = {
        "video_url": video_url,
        "video_path": video_path,
        "video_name": os.path.basename(video_path),
        "video_size_mb": round(os.path.getsize(video_path) / (1024*1024), 2),
        "source": "cloudinary" if "cloudinary" in video_url else "platform_upload",
        "timestamp": os.popen('date -u +%Y-%m-%dT%H:%M:%SZ').read().strip()
    }
    
    with open("tmp/video_metadata.json", "w") as f:
        json.dump(metadata, f, indent=2)


if __name__ == "__main__":
    main()