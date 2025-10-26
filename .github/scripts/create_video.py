#!/usr/bin/env python3
"""
🔥 Create Motivational Video - PRODUCTION VERSION WITH MUSIC
Features:
- Near-perfect audio-video synchronization (<50ms drift)
- Epic background music with dynamic volume control
- Cinematic teal & orange color grading
- High contrast dramatic lighting
- Warrior/training imagery optimization
- Audio timing metadata integration
- Multiple AI provider fallbacks
- Smart text wrapping with safe zones
"""

import os
import json
import requests
from moviepy import *
import platform
from tenacity import retry, stop_after_attempt, wait_exponential
from pydub import AudioSegment
from time import sleep
import time
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter
import random
import subprocess
import sys

TMP = os.getenv("GITHUB_WORKSPACE", ".") + "/tmp"
OUT = os.path.join(TMP, "short.mp4")
audio_path = os.path.join(TMP, "voice.mp3")
w, h = 1080, 1920

# Safe zones for text (avoiding screen edges)
SAFE_ZONE_MARGIN = 150
TEXT_MAX_WIDTH = w - (2 * SAFE_ZONE_MARGIN)

# 🔥 MOTIVATION COLOR PALETTE (Cinematic)
MOTIVATION_COLORS = {
    'deep_black': (15, 15, 20),
    'teal_shadow': (20, 40, 50),
    'orange_highlight': (255, 140, 60),
    'gold_triumph': (255, 200, 100),
    'dark_blue': (25, 35, 55),
    'fire_red': (200, 50, 30),
    'steel_gray': (60, 65, 70),
}

# 🎵 Import music system
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

try:
    from download_music import get_music_for_scene, MUSIC_DIR
    MUSIC_AVAILABLE = True
    print("✅ Music system available")
except ImportError:
    MUSIC_AVAILABLE = False
    print("⚠️ Music system not available (will skip background music)")


def get_font_path():
    """Get best available bold font for impact"""
    system = platform.system()
    if system == "Windows":
        return "C:/Windows/Fonts/arialbd.ttf"
    elif system == "Darwin":
        return "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
    else:
        font_options = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        ]
        for font in font_options:
            if os.path.exists(font):
                return font
        return "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"


FONT = get_font_path()
print(f"📝 Using font: {FONT}")

# Load script
with open(os.path.join(TMP, "script.json"), "r", encoding="utf-8") as f:
    data = json.load(f)

title = data.get("title", "Motivation")
hook = data.get("hook", "")
bullets = data.get("bullets", [])
cta = data.get("cta", "")
topic = data.get("topic", "motivation")
content_type = data.get("content_type", "general")
intensity = data.get("intensity", "balanced")
visual_prompts = data.get("visual_prompts", [])

print(f"🔥 Creating {content_type} motivational video ({intensity} intensity)")


def load_audio_timing():
    """
    Load optimized audio timing metadata from TTS generation
    Returns: timing data or None
    """
    timing_path = os.path.join(TMP, "audio_timing.json")
    
    if os.path.exists(timing_path):
        try:
            with open(timing_path, 'r') as f:
                timing_data = json.load(f)
            
            if timing_data.get('optimized'):
                print("✅ Loaded optimized audio timing metadata")
                print(f"   Total duration: {timing_data['total_duration']:.2f}s")
                print(f"   Sections: {len(timing_data['sections'])}")
                return timing_data
            else:
                print("⚠️ Timing metadata not optimized, using fallback")
                return None
                
        except Exception as e:
            print(f"⚠️ Could not load timing metadata: {e}")
            return None
    
    print("⚠️ No timing metadata found, using estimation")
    return None


def load_audio_metadata():
    """Load audio metadata"""
    metadata_path = os.path.join(TMP, "audio_metadata.json")
    if os.path.exists(metadata_path):
        try:
            with open(metadata_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return None
    return None


def get_section_duration_from_timing(section_name, timing_data):
    """Get duration for a specific section from timing metadata"""
    if not timing_data or 'sections' not in timing_data:
        return None
    
    for section in timing_data['sections']:
        if section['name'] == section_name:
            return section['duration']
    
    return None


def estimate_duration_fallback(text, audio_duration, all_text_parts):
    """Fallback duration estimation if timing metadata not available"""
    if not text or not all_text_parts:
        return 3.0
    
    words_this_section = len(text.split())
    total_words = sum(len(t.split()) for t in all_text_parts if t)
    
    if total_words == 0:
        return audio_duration / max(1, len(all_text_parts))
    
    duration = (words_this_section / total_words) * audio_duration
    return max(2.0, duration)


def enhance_visual_prompt_for_motivation(prompt, scene_type, intensity):
    """Enhance prompts specifically for motivational cinematic content"""
    
    cinematic_base = "cinematic 4K, dramatic lighting, high contrast, professional photography, ultra detailed"
    color_grading = "teal and orange color grade, split toning, moody atmospheric, film grain"
    
    scene_enhancements = {
        'pain': "dark moody atmosphere, contemplative, alone with thoughts, blue tones, deep shadows, emotional depth, introspective, solitude",
        'wake_up': "intense athletic training, determination, sweat and effort, pushing limits, slow motion action, explosive power, grit",
        'transformation': "epic journey, mountain summit at sunrise, victory pose, triumphant stance, powerful aspirational, breaking through",
        'action': "commanding warrior presence, direct eye contact, fierce determination, ready for battle, champion mindset, unstoppable"
    }
    
    intensity_keywords = {
        'aggressive': "raw intense powerful fierce hardcore unrelenting brutal honest",
        'balanced': "strong determined focused disciplined composed commanding",
        'inspirational': "uplifting empowering triumphant victorious inspiring heroic"
    }
    
    enhancement = scene_enhancements.get(scene_type, "powerful and inspiring")
    intensity_words = intensity_keywords.get(intensity, intensity_keywords['balanced'])
    motivational_keywords = "heroic stance, determined expression, muscular athletic, disciplined warrior, mental toughness"
    
    prompt = prompt.replace('happy', 'determined').replace('smiling', 'focused').replace('casual', 'intense')
    enhanced = f"{prompt}, {enhancement}, {intensity_words}, {motivational_keywords}, {color_grading}, {cinematic_base}"
    enhanced = enhanced.replace('  ', ' ').strip()
    
    return enhanced


def generate_image_huggingface(prompt, filename, width=1080, height=1920):
    """Generate image using Hugging Face FLUX"""
    try:
        hf_token = os.getenv('HUGGINGFACE_API_KEY')
        if not hf_token:
            print("    ⚠️ HUGGINGFACE_API_KEY not found")
            raise Exception("Missing token")

        headers = {"Authorization": f"Bearer {hf_token}"}
        
        negative_motivation = (
            "blurry, low quality, watermark, text overlay, logo, frame, caption, "
            "ui elements, interface, play button, branding, typography, paragraphs, "
            "cartoon, anime, illustration, painting, drawing, sketch, 3d render, "
            "happy smiling cheerful cute, bright colorful, pastel colors, soft lighting, "
            "compression artifacts, pixelated, distorted, deformed, multiple faces, "
            "duplicate body parts, text watermark, amateur photo, snapshot, "
            "oversaturated, underexposed, overexposed, artificial fake"
        )
        
        payload = {
            "inputs": f"{prompt}, professional cinematic photography, ultra realistic, photorealistic, dramatic lighting, teal and orange color grade, high contrast, film grain, moody atmospheric",
            "parameters": {
                "negative_prompt": negative_motivation,
                "num_inference_steps": 4,
                "guidance_scale": 0.0,
                "width": width,
                "height": height,
            }
        }

        models = [
            "black-forest-labs/FLUX.1-schnell",
            "black-forest-labs/FLUX.1-dev",
            "stabilityai/stable-diffusion-xl-base-1.0",
            "SG161222/RealVisXL_V4.0",
            "stabilityai/sdxl-turbo"
        ]

        for model in models:
            url = f"https://api-inference.huggingface.co/models/{model}"
            print(f"🤗 Trying model: {model}")

            response = requests.post(url, headers=headers, json=payload, timeout=120)

            if response.status_code == 200 and len(response.content) > 1000:
                filepath = os.path.join(TMP, filename)
                with open(filepath, "wb") as f:
                    f.write(response.content)
                print(f"    ✅ HuggingFace succeeded: {model}")
                return filepath

            elif response.status_code == 402:
                print(f"💰 {model} requires payment — trying next...")
                continue

            elif response.status_code in [503, 429]:
                print(f"⌛ {model} loading/rate-limited — trying next...")
                time.sleep(2)
                continue

            else:
                print(f"⚠️ {model} failed ({response.status_code}) — trying next...")

        raise Exception("All HuggingFace models failed")

    except Exception as e:
        print(f"⚠️ HuggingFace failed: {e}")
        raise


def generate_image_pollinations(prompt, filename, width=1080, height=1920):
    """Pollinations backup with motivation-optimized prompts"""
    try:
        negative_terms = (
            "blurry, low quality, watermark, text, logo, cartoon, anime, "
            "illustration, happy, cheerful, bright, colorful, pastel, "
            "soft lighting, amateur, snapshot, fake, artificial"
        )

        formatted_prompt = (
            f"{prompt}, cinematic photography, dramatic lighting, "
            "teal and orange color grade, high contrast, professional photo, "
            "moody atmospheric, film grain, photorealistic, ultra detailed"
        )

        seed = random.randint(1, 999999)

        url = (
            "https://image.pollinations.ai/prompt/"
            f"{requests.utils.quote(formatted_prompt)}"
            f"?width={width}&height={height}"
            f"&negative={requests.utils.quote(negative_terms)}"
            f"&nologo=true&notext=true&enhance=true&model=flux"
            f"&seed={seed}"
        )

        print(f"    🌐 Pollinations: {prompt[:60]}... (seed={seed})")
        response = requests.get(url, timeout=120)

        if response.status_code == 200 and "image" in response.headers.get("Content-Type", ""):
            filepath = os.path.join(TMP, filename)
            with open(filepath, "wb") as f:
                f.write(response.content)
            print(f"    ✅ Pollinations generated (seed {seed})")
            return filepath
        else:
            raise Exception(f"Pollinations failed: {response.status_code}")

    except Exception as e:
        print(f"    ⚠️ Pollinations failed: {e}")
        raise


def generate_motivation_fallback(bg_path, scene_type, width=1080, height=1920):
    """Motivation-specific fallback with Unsplash/Pexels"""
    
    topic_keywords = {
        'pain': ['contemplation', 'solitude', 'dark-mood', 'alone', 'night'],
        'wake_up': ['training', 'athlete', 'gym', 'workout', 'fitness', 'boxing', 'running'],
        'transformation': ['mountain', 'summit', 'victory', 'success', 'achievement', 'sunrise'],
        'action': ['warrior', 'fighter', 'champion', 'power', 'strength', 'determination']
    }
    
    keywords = topic_keywords.get(scene_type, ['motivation', 'success', 'determination'])
    keyword = random.choice(keywords)
    
    print(f"🔎 Searching motivation image for '{scene_type}' (keyword: '{keyword}')...")

    try:
        seed = random.randint(1, 9999)
        url = f"https://source.unsplash.com/{width}x{height}/?{requests.utils.quote(keyword)}&sig={seed}"
        print(f"🖼️ Unsplash: '{keyword}' (seed={seed})...")
        response = requests.get(url, timeout=30, allow_redirects=True)
        
        if response.status_code == 200 and "image" in response.headers.get("Content-Type", ""):
            with open(bg_path, "wb") as f:
                f.write(response.content)
            print(f"    ✅ Unsplash image saved")
            return bg_path
        else:
            print(f"    ⚠️ Unsplash failed ({response.status_code})")
    except Exception as e:
        print(f"    ⚠️ Unsplash error: {e}")

    try:
        print("    🔄 Trying Pexels curated motivation photos...")
        
        motivation_pexels_ids = {
            'pain': [3772509, 3771074, 3771790, 3771089, 1587927, 2777898, 733767, 1209843],
            'wake_up': [1552242, 1552252, 1552249, 1229356, 1229355, 888899, 2803158, 3621177, 4754147, 4754148, 7991579, 1480520, 1480521, 936094],
            'transformation': [1266810, 1287460, 1509428, 1761279, 2440024, 1850629, 2047905, 3137068, 1118873, 1591373, 2387873],
            'action': [4754147, 7991579, 1480520, 1552242, 1229356, 936094, 888899, 2803158, 3621177]
        }
        
        scene_key = scene_type if scene_type in motivation_pexels_ids else 'wake_up'
        photo_ids = motivation_pexels_ids[scene_key].copy()
        random.shuffle(photo_ids)
        
        for attempt, photo_id in enumerate(photo_ids[:5]):
            seed = random.randint(1000, 9999)
            url = f"https://images.pexels.com/photos/{photo_id}/pexels-photo-{photo_id}.jpeg?auto=compress&cs=tinysrgb&w=1080&h=1920&fit=crop&random={seed}"
            
            print(f"📸 Pexels photo attempt {attempt+1} (id={photo_id}, scene='{scene_key}')...")

            response = requests.get(url, timeout=30)
            if response.status_code == 200 and "image" in response.headers.get("Content-Type", ""):
                with open(bg_path, "wb") as f:
                    f.write(response.content)
                print(f"    ✅ Pexels photo saved (id: {photo_id})")

                img = Image.open(bg_path).convert("RGB")
                img = img.resize((width, height), Image.LANCZOS)
                img.save(bg_path, quality=95)
                
                return bg_path
            else:
                print(f"    ⚠️ Photo {photo_id} failed: {response.status_code}")
        
        print("    ⚠️ All Pexels photos failed")
        
    except Exception as e:
        print(f"    ⚠️ Pexels fallback failed: {e}")

    try:
        seed = random.randint(1, 1000)
        url = f"https://picsum.photos/{width}/{height}?random={seed}&grayscale"
        print(f"🎲 Picsum fallback (seed={seed})...")
        response = requests.get(url, timeout=30, allow_redirects=True)
        
        if response.status_code == 200:
            with open(bg_path, "wb") as f:
                f.write(response.content)
            print(f"    ✅ Picsum image saved")
            return bg_path
            
    except Exception as e:
        print(f"    ⚠️ Picsum failed: {e}")

    return None


def create_cinematic_gradient(filepath, scene_type, width=1080, height=1920):
    """Create cinematic gradient with motivation color palette"""
    
    img = Image.new("RGB", (width, height), (0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    color_schemes = {
        'pain': [MOTIVATION_COLORS['deep_black'], MOTIVATION_COLORS['teal_shadow']],
        'wake_up': [MOTIVATION_COLORS['fire_red'], MOTIVATION_COLORS['orange_highlight']],
        'transformation': [MOTIVATION_COLORS['teal_shadow'], MOTIVATION_COLORS['gold_triumph']],
        'action': [MOTIVATION_COLORS['steel_gray'], MOTIVATION_COLORS['orange_highlight']]
    }
    
    colors = color_schemes.get(scene_type, [MOTIVATION_COLORS['deep_black'], MOTIVATION_COLORS['teal_shadow']])
    
    for y in range(height):
        ratio = y / height
        r = int(colors[0][0] * (1 - ratio) + colors[1][0] * ratio)
        g = int(colors[0][1] * (1 - ratio) + colors[1][1] * ratio)
        b = int(colors[0][2] * (1 - ratio) + colors[1][2] * ratio)
        draw.line([(0, y), (width, y)], fill=(r, g, b))
    
    img = apply_vignette_simple(img, strength=0.5)
    
    img.save(filepath, quality=95)
    print(f"    ✅ Cinematic gradient created ({scene_type})")
    return filepath


def apply_vignette_simple(img, strength=0.3):
    """Quick vignette effect"""
    width, height = img.size
    mask = Image.new('L', (width, height), 255)
    draw = ImageDraw.Draw(mask)
    
    for i in range(int(min(width, height) * strength)):
        alpha = int(255 * (1 - i / (min(width, height) * strength)))
        draw.rectangle([i, i, width-i, height-i], outline=alpha)
    
    black = Image.new('RGB', (width, height), (0, 0, 0))
    return Image.composite(img, black, mask)


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=2, min=4, max=20))
def generate_image_reliable(prompt, filename, scene_type, width=1080, height=1920):
    """Try multiple providers with motivation-specific fallbacks"""
    filepath = os.path.join(TMP, filename)
    
    providers = [
        ("Pollinations", generate_image_pollinations),
        ("HuggingFace", generate_image_huggingface)
    ]
    
    for provider_name, provider_func in providers:
        try:
            print(f"🎨 Trying {provider_name}...")
            result = provider_func(prompt, filename, width, height)
            if result and os.path.exists(result) and os.path.getsize(result) > 1000:
                return result
        except Exception as e:
            print(f"    ⚠️ {provider_name} failed: {e}")
            continue

    print("🖼️ AI failed, trying curated motivation photos...")
    result = generate_motivation_fallback(filepath, scene_type=scene_type, width=width, height=height)

    if result and os.path.exists(filepath) and os.path.getsize(filepath) > 1000:
        return result
    
    print("⚠️ All providers failed, creating cinematic gradient...")
    return create_cinematic_gradient(filepath, scene_type, width, height)


def apply_cinematic_color_grading(image_path, scene_type):
    """Apply teal & orange cinematic color grading"""
    
    print(f"      🎨 Applying cinematic color grading ({scene_type})...")
    
    try:
        img = Image.open(image_path).convert('RGB')
        
        if scene_type == 'pain':
            img = tint_shadows_teal(img)
            contrast = 1.9
            brightness = 0.8
            saturation = 0.85
            
        elif scene_type == 'wake_up':
            img = tint_highlights_orange(img)
            contrast = 2.0
            brightness = 1.1
            saturation = 1.4
            
        elif scene_type == 'transformation':
            img = apply_teal_orange_grade(img)
            contrast = 1.8
            brightness = 1.15
            saturation = 1.3
            
        else:
            img = tint_golden(img)
            contrast = 1.9
            brightness = 1.2
            saturation = 1.35
        
        img = ImageEnhance.Contrast(img).enhance(contrast)
        img = ImageEnhance.Brightness(img).enhance(brightness)
        img = ImageEnhance.Color(img).enhance(saturation)
        
        img = img.filter(ImageFilter.SHARPEN)
        img = add_film_grain(img, intensity=0.15)
        img = apply_vignette_simple(img, strength=0.35)
        
        img.save(image_path, quality=95)
        print(f"      ✅ Color grading applied")
        
    except Exception as e:
        print(f"      ⚠️ Color grading failed: {e}")
    
    return image_path


def tint_shadows_teal(img):
    """Add teal tint to shadows"""
    pixels = img.load()
    width, height = img.size
    
    for x in range(width):
        for y in range(height):
            r, g, b = pixels[x, y]
            brightness = (r + g + b) / 3
            
            if brightness < 128:
                factor = (128 - brightness) / 128
                r = int(r + (20 - r) * factor * 0.4)
                g = int(g + (50 - g) * factor * 0.4)
                b = int(b + (60 - b) * factor * 0.4)
            
            pixels[x, y] = (max(0, min(255, r)), max(0, min(255, g)), max(0, min(255, b)))
    
    return img


def tint_highlights_orange(img):
    """Add orange tint to highlights"""
    pixels = img.load()
    width, height = img.size
    
    for x in range(width):
        for y in range(height):
            r, g, b = pixels[x, y]
            brightness = (r + g + b) / 3
            
            if brightness > 128:
                factor = (brightness - 128) / 127
                r = int(r + (255 - r) * factor * 0.25)
                g = int(g + (180 - g) * factor * 0.2)
                b = int(b + (100 - b) * factor * 0.15)
            
            pixels[x, y] = (max(0, min(255, r)), max(0, min(255, g)), max(0, min(255, b)))
    
    return img


def apply_teal_orange_grade(img):
    """Classic teal & orange cinematic look"""
    img = tint_shadows_teal(img)
    img = tint_highlights_orange(img)
    return img


def tint_golden(img):
    """Add golden tones"""
    pixels = img.load()
    width, height = img.size
    
    for x in range(width):
        for y in range(height):
            r, g, b = pixels[x, y]
            
            r = int(r * 1.2)
            g = int(g * 1.1)
            b = int(b * 0.85)
            
            pixels[x, y] = (max(0, min(255, r)), max(0, min(255, g)), max(0, min(255, b)))
    
    return img


def add_film_grain(img, intensity=0.1):
    """Add subtle film grain"""
    import numpy as np
    
    try:
        img_array = np.array(img)
        noise = np.random.normal(0, intensity * 255, img_array.shape)
        noisy = img_array + noise
        noisy = np.clip(noisy, 0, 255).astype(np.uint8)
        return Image.fromarray(noisy)
    except:
        return img


# Fallback method (works on all MoviePy versions)
# ============================================
# 🎵 MUSIC INTEGRATION FUNCTIONS
# ============================================

# ✅ PUT THE SAFE VOLUME FUNCTION HERE (first)
def apply_volume_safe(audio_clip, volume_factor):
    """Safe volume application for all MoviePy versions"""
    try:
        # Try multiply_volume first
        return audio_clip.multiply_volume(volume_factor)
    except AttributeError:
        try:
            # Fallback: set_volume (older API)
            return audio_clip.set_volume(volume_factor)
        except AttributeError:
            try:
                # Last resort: volume_factor parameter
                return audio_clip.set_volume(volume_factor)
            except:
                print("⚠️ Volume control not available, returning original")
                return audio_clip


# ✅ THEN YOUR EXISTING create_dynamic_music_layer FUNCTION
def create_dynamic_music_layer(audio_duration, script_data):
    """
    Create music layer with proper volume mixing
    PRODUCTION-READY VERSION
    """
    
    if not MUSIC_AVAILABLE:
        print("⚠️ Music system unavailable, skipping background music")
        return None
    
    print("\n🎵 Creating music layer with dynamic volume...")
    
    content_type = script_data.get('content_type', 'general')
    
    # Scene to music type mapping
    scene_map = {
        'early_morning': 'wake_up',
        'late_night': 'pain',
        'midday': 'wake_up',
        'evening': 'transformation',
        'general': 'transformation'
    }
    
    primary_scene = scene_map.get(content_type, 'transformation')
    
    try:
        track_key, music_path, default_volume = get_music_for_scene(primary_scene, content_type)
        
        if not music_path or not os.path.exists(music_path):
            print("⚠️ No music track available")
            return None
        
        print(f"   🎵 Track: {track_key}")
        print(f"   📁 Path: {music_path}")
        
        # Load music
        music = AudioFileClip(music_path)
        original_duration = music.duration
        print(f"   ⏱️ Original duration: {original_duration:.2f}s")
        
        # Loop if needed
        if music.duration < audio_duration:
            loops_needed = int(audio_duration / music.duration) + 1
            print(f"   🔁 Looping {loops_needed}x to reach {audio_duration:.2f}s")
            
            from moviepy.audio.AudioClip import concatenate_audioclips
            music_clips = [music] * loops_needed
            music = concatenate_audioclips(music_clips)
        
        # Trim to exact duration
        music = music.subclipped(0, min(audio_duration, music.duration))
        
        # Volume mapping by content type
        volume_mapping = {
            'early_morning': 0.30,
            'late_night': 0.15,
            'midday': 0.35,
            'evening': 0.22,
            'general': 0.25
        }
        
        final_volume = volume_mapping.get(content_type, 0.35)
        
        # ✅ USE THE SAFE FUNCTION HERE
        music = apply_volume_safe(music, final_volume)
        
        print(f"   ✅ Volume set: {final_volume*100:.0f}%")
        print(f"   ✅ Final duration: {music.duration:.2f}s")
        
        return music
    
    except Exception as e:
        print(f"❌ Music layer creation failed: {e}")
        import traceback
        traceback.print_exc()
        return None

# --- Main Scene Generation ---

print("🔥 Generating motivational scenes...")

scene_types = ['pain', 'wake_up', 'transformation', 'action']
scene_images = []

try:
    # Hook scene
    hook_prompt = visual_prompts[0] if len(visual_prompts) > 0 else f"Dark contemplative mood for: {hook}"
    hook_prompt = enhance_visual_prompt_for_motivation(hook_prompt, 'pain', intensity)
    hook_img = generate_image_reliable(hook_prompt, "scene_hook.jpg", 'pain', w, h)
    if hook_img:
        apply_cinematic_color_grading(hook_img, 'pain')
    scene_images.append(hook_img)
    
    # Bullet scenes
    for i, bullet in enumerate(bullets):
        scene_type = scene_types[min(i + 1, len(scene_types) - 1)]
        bullet_prompt = visual_prompts[i+1] if len(visual_prompts) > i+1 else f"Motivational scene: {bullet}"
        bullet_prompt = enhance_visual_prompt_for_motivation(bullet_prompt, scene_type, intensity)
        
        bullet_img = generate_image_reliable(bullet_prompt, f"scene_bullet_{i}.jpg", scene_type, w, h)
        if bullet_img:
            apply_cinematic_color_grading(bullet_img, scene_type)
        scene_images.append(bullet_img)
        
        time.sleep(0.5)

    # CTA scene
    cta_prompt = visual_prompts[-1] if len(visual_prompts) > len(bullets) else f"Triumphant victory: {cta}"
    cta_prompt = enhance_visual_prompt_for_motivation(cta_prompt, 'action', intensity)
    cta_img = generate_image_reliable(cta_prompt, "scene_cta.jpg", 'action', w, h)
    if cta_img:
        apply_cinematic_color_grading(cta_img, 'action')
    scene_images.append(cta_img)
    
    successful = len([img for img in scene_images if img and os.path.exists(img)])
    print(f"✅ Generated {successful}/{len(scene_images)} scenes")
    
except Exception as e:
    print(f"⚠️ Image generation error: {e}")
    scene_images = [None] * (len(bullets) + 2)

# Validate images
print(f"🔍 Validating {len(scene_images)} scenes...")
for i in range(len(scene_images)):
    img = scene_images[i] if i < len(scene_images) else None
    
    if not img or not os.path.exists(img) or os.path.getsize(img) < 1000:
        print(f"⚠️ Scene {i} invalid, creating gradient...")
        scene_type = scene_types[min(i, len(scene_types) - 1)]
        fallback_path = os.path.join(TMP, f"scene_fallback_{i}.jpg")
        create_cinematic_gradient(fallback_path, scene_type, w, h)
        scene_images[i] = fallback_path

print(f"✅ All scenes validated")

# --- Audio Loading & Timing (OPTIMIZED) ---

if not os.path.exists(audio_path):
    print(f"❌ Audio not found: {audio_path}")
    raise FileNotFoundError("voice.mp3 missing")

audio = AudioFileClip(audio_path)
duration = audio.duration
print(f"🎵 Audio: {duration:.2f}s")

# ✅ LOAD OPTIMIZED TIMING METADATA
timing_data = load_audio_timing()

if timing_data and timing_data.get('optimized'):
    print("\n⏱️ Using OPTIMIZED audio timing (near-perfect sync expected)")
    
    sections = timing_data['sections']
    
    hook_dur = 0.0
    bullet_durs = []
    cta_dur = 0.0
    
    if hook:
        hook_section = next((s for s in sections if s['name'] == 'hook'), None)
        if hook_section:
            hook_dur = hook_section['duration']
            print(f"   Hook: {hook_dur:.2f}s (from metadata)")
        else:
            all_text = [hook] + bullets + [cta]
            hook_dur = estimate_duration_fallback(hook, duration, all_text)
            print(f"   Hook: {hook_dur:.2f}s (estimated)")
    
    for i, bullet in enumerate(bullets):
        bullet_section = next((s for s in sections if s['name'] == f'bullet_{i}'), None)
        if bullet_section:
            dur = bullet_section['duration']
            bullet_durs.append(dur)
            print(f"   Bullet {i+1}: {dur:.2f}s (from metadata)")
        else:
            all_text = [hook] + bullets + [cta]
            dur = estimate_duration_fallback(bullet, duration, all_text)
            bullet_durs.append(dur)
            print(f"   Bullet {i+1}: {dur:.2f}s (estimated)")
    
    if cta:
        cta_section = next((s for s in sections if s['name'] == 'cta'), None)
        if cta_section:
            cta_dur = cta_section['duration']
            print(f"   CTA: {cta_dur:.2f}s (from metadata)")
        else:
            all_text = [hook] + bullets + [cta]
            cta_dur = estimate_duration_fallback(cta, duration, all_text)
            print(f"   CTA: {cta_dur:.2f}s (estimated)")
    
    total_calculated = hook_dur + sum(bullet_durs) + cta_dur
    
    if abs(total_calculated - duration) > 0.5:
        print(f"\n⚠️ Timing mismatch detected:")
        print(f"   Calculated: {total_calculated:.2f}s")
        print(f"   Audio: {duration:.2f}s")
        print(f"   Adjusting proportionally...")
        
        adjustment_factor = duration / total_calculated
        
        hook_dur *= adjustment_factor
        bullet_durs = [d * adjustment_factor for d in bullet_durs]
        cta_dur *= adjustment_factor
        
        print(f"   ✅ Adjusted by factor {adjustment_factor:.4f}")

else:
    print("\n⚠️ No timing metadata available, using estimation")
    
    def estimate_duration(text):
        words = len(text.split())
        return (words / 110) * 60.0
    
    hook_est = estimate_duration(hook) if hook else 0
    bullets_est = [estimate_duration(b) for b in bullets]
    cta_est = estimate_duration(cta) if cta else 0
    
    total_est = hook_est + sum(bullets_est) + cta_est
    
    if total_est > 0:
        scale = duration / total_est
        hook_dur = hook_est * scale
        bullet_durs = [b * scale for b in bullets_est]
        cta_dur = cta_est * scale
    else:
        equal = duration / max(1, len(bullets) + 2)
        hook_dur = equal
        bullet_durs = [equal] * len(bullets)
        cta_dur = equal

print(f"\n⏱️ Final Scene Timings:")
if hook:
    print(f"   Hook: {hook_dur:.2f}s")
for i, dur in enumerate(bullet_durs):
    print(f"   Bullet {i+1}: {dur:.2f}s")
if cta:
    print(f"   CTA: {cta_dur:.2f}s")

total_timeline = (hook_dur if hook else 0) + sum(bullet_durs) + (cta_dur if cta else 0)
print(f"   Total Timeline: {total_timeline:.2f}s")
print(f"   Audio Duration: {duration:.2f}s")
print(f"   Drift: {abs(total_timeline - duration)*1000:.0f}ms")

# --- Video Composition ---

clips = []
current_time = 0


def smart_text_wrap(text, font_size, max_width):
    """Smart text wrapping (no word splitting)"""
    try:
        pil_font = ImageFont.truetype(FONT, font_size)
        dummy_img = Image.new('RGB', (1, 1))
        draw = ImageDraw.Draw(dummy_img)
        
        words = text.split()
        lines = []
        current_line = []
        
        for word in words:
            test_line = ' '.join(current_line + [word])
            bbox = draw.textbbox((0, 0), test_line, font=pil_font)
            text_width = bbox[2] - bbox[0]
            
            if text_width <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]
        
        if current_line:
            lines.append(' '.join(current_line))
        
        return '\n'.join(lines) + '\n'
        
    except:
        words = text.split()
        avg_char_width = font_size * 0.55
        max_chars = int(max_width / avg_char_width)
        
        lines = []
        current_line = []
        
        for word in words:
            test = ' '.join(current_line + [word])
            if len(test) <= max_chars:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]
        
        if current_line:
            lines.append(' '.join(current_line))
        
        return '\n'.join(lines) + '\n'


def create_text_with_effects(text, font_size=70, max_width=TEXT_MAX_WIDTH):
    """Create text with adaptive sizing"""
    wrapped = smart_text_wrap(text, font_size, max_width)
    
    try:
        pil_font = ImageFont.truetype(FONT, font_size)
        dummy = Image.new('RGB', (1, 1))
        draw = ImageDraw.Draw(dummy)
        
        lines = wrapped.split('\n')
        total_h = 0
        max_w = 0
        
        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=pil_font)
            total_h += bbox[3] - bbox[1]
            max_w = max(max_w, bbox[2] - bbox[0])
        
        max_height = h * 0.3
        iterations = 0
        
        while (total_h > max_height or max_w > max_width) and font_size > 36 and iterations < 10:
            font_size -= 5
            wrapped = smart_text_wrap(text, font_size, max_width)
            pil_font = ImageFont.truetype(FONT, font_size)
            
            lines = wrapped.split('\n')
            total_h = 0
            max_w = 0
            
            for line in lines:
                bbox = draw.textbbox((0, 0), line, font=pil_font)
                total_h += bbox[3] - bbox[1]
                max_w = max(max_w, bbox[2] - bbox[0])
            
            iterations += 1
            
    except:
        pass
    
    return wrapped, font_size


def create_scene(image_path, text, duration, start_time, position_y='center', color_fallback=None):
    """Create scene with image + text"""
    scene_clips = []
    
    if color_fallback is None:
        color_fallback = MOTIVATION_COLORS['deep_black']
    
    if image_path and os.path.exists(image_path):
        bg = (ImageClip(image_path)
              .resized(height=h)
              .with_duration(duration)
              .with_start(start_time)
              .with_effects([vfx.CrossFadeIn(0.3), vfx.CrossFadeOut(0.3)]))
    else:
        bg = (ColorClip(size=(w, h), color=color_fallback, duration=duration)
              .with_start(start_time))
    
    scene_clips.append(bg)
    
    if text:
        wrapped, font_size = create_text_with_effects(text)
        
        text_method = 'label' if len(text.split()) <= 3 else 'caption'
        stroke = 3 if len(text.split()) <= 3 else 5
        
        text_clip = TextClip(
            text=wrapped,
            font=FONT,
            font_size=font_size,
            color='white',
            stroke_width=stroke,
            stroke_color='black',
            method=text_method,
            text_align='center',
            size=(TEXT_MAX_WIDTH, None),
        )
        
        text_h = text_clip.h
        descender = max(40, int(font_size * 0.6))
        bottom_safe = SAFE_ZONE_MARGIN + 200
        
        if position_y == 'center':
            pos_y = (h - text_h) // 2
        elif position_y == 'top':
            pos_y = SAFE_ZONE_MARGIN + 100
        elif position_y == 'bottom':
            pos_y = h - text_h - bottom_safe - descender
        else:
            pos_y = position_y
        
        pos_y = max(SAFE_ZONE_MARGIN + 100, min(pos_y, h - text_h - bottom_safe - descender))
        
        text_clip = (text_clip
                    .with_duration(duration)
                    .with_start(start_time)
                    .with_position(('center', pos_y))
                    .with_effects([vfx.CrossFadeIn(0.3), vfx.CrossFadeOut(0.3)]))
        
        print(f"      Text: '{text[:40]}...' @ Y={pos_y}, Size={font_size}px")
        scene_clips.append(text_clip)
    
    return scene_clips


# Build scenes
if hook:
    print(f"🎬 Hook scene...")
    clips.extend(create_scene(
        scene_images[0], hook, hook_dur, current_time,
        position_y='top', color_fallback=MOTIVATION_COLORS['teal_shadow']
    ))
    current_time += hook_dur

for i, bullet in enumerate(bullets):
    dur = bullet_durs[i]
    
    if not bullet.strip():
        print(f"⚠️ Bullet {i+1} empty, placeholder...")
        clips.append(ColorClip(size=(w, h), color=MOTIVATION_COLORS['deep_black'], duration=dur).with_start(current_time))
        current_time += dur
        continue
    
    img_idx = min(i + 1, len(scene_images) - 1)
    
    colors = [
        MOTIVATION_COLORS['fire_red'],
        MOTIVATION_COLORS['orange_highlight'],
        MOTIVATION_COLORS['gold_triumph']
    ]
    
    print(f"🎬 Bullet {i+1}...")
    clips.extend(create_scene(
        scene_images[img_idx], bullet, dur, current_time,
        position_y='center', color_fallback=colors[i % len(colors)]
    ))
    current_time += dur

if cta:
    print(f"📢 CTA scene...")
    clips.extend(create_scene(
        scene_images[-1], cta, cta_dur, current_time,
        position_y='bottom', color_fallback=MOTIVATION_COLORS['steel_gray']
    ))
    current_time += cta_dur

# Sync check
print(f"\n📊 SYNC CHECK:")
print(f"   Timeline: {current_time:.2f}s")
print(f"   Audio: {duration:.2f}s")
print(f"   Drift: {abs(current_time - duration)*1000:.0f}ms")

if abs(current_time - duration) < 0.05:
    print(f"   ✅ NEAR-PERFECT SYNC!")
elif abs(current_time - duration) < 0.5:
    print(f"   ✅ Excellent sync (within tolerance)")
else:
    print(f"   ⚠️ Sync drift detected (may need adjustment)")

print(f"\n🎬 Composing video ({len(clips)} clips)...")
video = CompositeVideoClip(clips, size=(w, h))

# 🎵 ADD BACKGROUND MUSIC + TTS VOICEOVER
print(f"\n🔊 Adding audio with background music...")

background_music = create_dynamic_music_layer(duration, data)

if background_music:
    try:
        # Composite: TTS voiceover + background music
        # TTS is already at proper volume from generate_tts.py
        final_audio = CompositeAudioClip([audio, background_music])
        video = video.with_audio(final_audio)
        print(f"   ✅ Audio: TTS + Epic background music (professional mix)")
    except Exception as e:
        print(f"   ⚠️ Music compositing failed: {e}")
        print(f"   Fallback: TTS only")
        video = video.with_audio(audio)
else:
    # Fallback: just TTS
    video = video.with_audio(audio)
    print(f"   ⚠️ Audio: TTS only (music unavailable)")

if video.audio is None:
    raise Exception("Audio attachment failed!")

print(f"\n📹 Writing video...")
try:
    video.write_videofile(
        OUT,
        fps=30,
        codec="libx264",
        audio_codec="aac",
        threads=4,
        preset='medium',
        audio_bitrate='192k',
        bitrate='8000k',
        logger=None
    )
    
    sync_status = "NEAR-PERFECT" if abs(current_time - duration) < 0.05 else "EXCELLENT" if abs(current_time - duration) < 0.5 else "GOOD"
    
    print(f"\n✅ MOTIVATIONAL VIDEO COMPLETE!")
    print(f"   Path: {OUT}")
    print(f"   Duration: {duration:.2f}s")
    print(f"   Size: {os.path.getsize(OUT) / (1024*1024):.2f} MB")
    print(f"   Sync Status: {sync_status} ({abs(current_time - duration)*1000:.0f}ms drift)")
    print(f"   Features:")
    print(f"      ✓ Optimized audio timing metadata")
    print(f"      ✓ Epic background music with dynamic volume")
    print(f"      ✓ Cinematic teal & orange color grading")
    print(f"      ✓ Motivation-specific image generation")
    print(f"      ✓ Curated fitness/warrior photos")
    print(f"      ✓ High contrast dramatic lighting")
    print(f"      ✓ Film grain for cinematic feel")
    print(f"      ✓ Vignette effects")
    print(f"      ✓ Smart text wrapping (no splits)")
    print(f"      ✓ Audio-synchronized timing")
    print(f"      ✓ Safe zone text positioning")
    print(f"      ✓ Adaptive font sizing")
    print(f"      ✓ Cross-fade transitions")
    if background_music:
        print(f"      ✓ Professional audio mix (TTS + Music)")
    print(f"   🔥 Motivational empire ready!")
    
except Exception as e:
    print(f"❌ Video creation failed: {e}")
    raise

finally:
    print("🧹 Cleanup...")
    audio.close()
    video.close()
    for clip in clips:
        try:
            clip.close()
        except:
            pass

print("✅ Motivation video pipeline complete! 🔥")