#!/usr/bin/env python3
"""
🔥 Generate Motivational Thumbnail - ROBUST VERSION
Features:
- Dark dramatic backgrounds
- CAPS power words
- High contrast warrior imagery
- Cinematic teal/orange grading
- Motivation-specific photo sources
- Aggressive bold typography
"""

import os
import json
import requests
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
from io import BytesIO
import platform
from tenacity import retry, stop_after_attempt, wait_exponential
from time import sleep
import time
import textwrap
import random
import re

TMP = os.getenv("GITHUB_WORKSPACE", ".") + "/tmp"

# 🔥 MOTIVATION COLOR PALETTE (Dark & Powerful)
MOTIVATION_COLORS = {
    'deep_black': (15, 15, 20),
    'teal_shadow': (20, 40, 50),
    'orange_highlight': (255, 140, 60),
    'gold_power': (255, 215, 0),
    'fire_red': (220, 50, 30),
    'steel_gray': (60, 65, 70),
}


def get_font_path(size=90, bold=True):
    """Get boldest available font for POWER"""
    system = platform.system()
    font_paths = []
    
    if system == "Windows":
        font_paths = [
            "C:/Windows/Fonts/impact.ttf",  # IMPACT first
            "C:/Windows/Fonts/arialbd.ttf",
            "C:/Windows/Fonts/ariblk.ttf",
        ]
    elif system == "Darwin":
        font_paths = [
            "/System/Library/Fonts/Supplemental/Impact.ttf",
            "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
            "/Library/Fonts/Arial Black.ttf",
        ]
    else:
        font_paths = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        ]
    
    for font_path in font_paths:
        if os.path.exists(font_path):
            try:
                return ImageFont.truetype(font_path, size)
            except Exception as e:
                print(f"⚠️ Could not load {font_path}: {e}")
    
    print("⚠️ Using default font")
    return ImageFont.load_default()


# Load script
# Load script
with open(os.path.join(TMP, "script.json"), "r", encoding="utf-8") as f:
    data = json.load(f)

title = data.get("title", "MOTIVATION")
topic = data.get("topic", "motivation")
hook = data.get("hook", "")
key_phrase = data.get("key_phrase", "")
content_type = data.get("content_type", "general")

# 🔥 SMART TEXT SELECTION (FIXED)
display_text = None

# Priority 1: Key phrase (if substantial)
if key_phrase and len(key_phrase) > 5:
    display_text = key_phrase
    print(f"🔥 Using KEY PHRASE: {display_text}")

# Priority 2: Hook (if shorter and substantial)
elif hook and len(hook) > 5 and len(hook) < len(title):
    display_text = hook
    print(f"🎯 Using HOOK: {display_text}")

# Priority 3: Title
else:
    display_text = title
    print(f"📝 Using TITLE: {display_text}")

# NOW uppercase the selected text
display_text = display_text.upper()

# Try to extract CAPS words ONLY if we don't have a key_phrase
if not key_phrase or len(key_phrase) < 5:
    # Extract CAPS words from the display_text to enhance it
    caps_words = re.findall(r'\b[A-Z]{2,}\b', display_text)
    
    # If we found a short punchy CAPS phrase (2-5 words), use it instead
    if caps_words and 2 <= len(caps_words) <= 5:
        caps_phrase = ' '.join(caps_words)
        # Only use it if it's significantly shorter (more impactful)
        if len(caps_phrase) < len(display_text) * 0.6:
            display_text = caps_phrase
            print(f"💥 Extracted CAPS PHRASE: {display_text}")

print(f"📊 Final thumbnail text: {display_text}")
print(f"   Length: {len(display_text)} chars")

# Canvas dimensions
w = 720
h = 1280

# Safe zones
SAFE_ZONE_MARGIN = 50
TEXT_MAX_WIDTH = w - (2 * SAFE_ZONE_MARGIN)


def generate_thumbnail_huggingface(prompt):
    """🔥 Generate motivational thumbnail using HuggingFace"""
    try:
        hf_token = os.getenv('HUGGINGFACE_API_KEY')
        if not hf_token:
            raise Exception("Missing HUGGINGFACE_API_KEY")

        headers = {"Authorization": f"Bearer {hf_token}"}
        
        # 🔥 Motivation-specific negative prompt
        negative_motivation = (
            "blurry, low quality, watermark, text overlay, logo, ui, interface, "
            "happy, cheerful, smiling, bright, colorful, pastel, soft, cute, "
            "cartoon, anime, illustration, painting, 3d render, fake, artificial, "
            "compression, pixelated, distorted, deformed, amateur"
        )
        
        payload = {
            "inputs": f"{prompt}, cinematic dramatic photography, teal and orange color grade, high contrast, moody atmospheric, professional, ultra detailed, no text",
            "parameters": {
                "negative_prompt": negative_motivation,
                "num_inference_steps": 4,
                "guidance_scale": 0.0,
                "width": 720,
                "height": 1280,
            }
        }

        models = [
            "black-forest-labs/FLUX.1-schnell",
            "stabilityai/stable-diffusion-xl-base-1.0",
            "SG161222/RealVisXL_V4.0",
            "stabilityai/sdxl-turbo"
        ]

        for model in models:
            url = f"https://api-inference.huggingface.co/models/{model}"
            print(f"🤗 Trying {model}")

            response = requests.post(url, headers=headers, json=payload, timeout=120)

            if response.status_code == 200 and len(response.content) > 1000:
                print(f"✅ {model} succeeded")
                return response.content
            elif response.status_code == 402:
                print(f"💰 {model} requires payment")
                continue
            elif response.status_code in [503, 429]:
                print(f"⌛ {model} loading/rate-limited")
                time.sleep(2)
                continue

        raise Exception("All HuggingFace models failed")

    except Exception as e:
        print(f"⚠️ HuggingFace failed: {e}")
        raise


def generate_thumbnail_pollinations(prompt):
    """🔥 Pollinations backup"""
    try:
        negative = (
            "text, logo, watermark, ui, interface, overlay, branding, "
            "happy, cheerful, bright, colorful, cartoon, anime, soft"
        )

        enhanced = (
            f"{prompt}, cinematic photography, dramatic lighting, "
            "teal and orange color grade, high contrast, moody, "
            "professional photo, ultra detailed, no text, no logos"
        )

        seed = random.randint(1, 999999)
        url = (
            f"https://image.pollinations.ai/prompt/{requests.utils.quote(enhanced)}"
            f"?width=720&height=1280&negative={requests.utils.quote(negative)}"
            f"&nologo=true&notext=true&enhance=true&model=flux&seed={seed}"
        )

        print(f"🌐 Pollinations (seed={seed})")
        response = requests.get(url, timeout=120)

        if response.status_code == 200:
            print(f"✅ Pollinations succeeded")
            return response.content

        raise Exception(f"Pollinations failed: {response.status_code}")

    except Exception as e:
        print(f"⚠️ Pollinations failed: {e}")
        raise


def generate_motivation_fallback(bg_path, content_type):
    """🔥 Motivation-specific fallback with curated photos"""
    
    # Content-type specific keywords
    keywords_map = {
        'early_morning': ['training', 'athlete', 'gym', 'workout', 'fitness'],
        'late_night': ['night', 'dark', 'solitude', 'contemplation', 'alone'],
        'midday': ['power', 'strength', 'determination', 'focused'],
        'evening': ['sunset', 'reflection', 'victory', 'achievement'],
        'general': ['motivation', 'success', 'warrior', 'champion']
    }
    
    keywords = keywords_map.get(content_type, keywords_map['general'])
    keyword = random.choice(keywords)
    
    print(f"🔎 Searching motivation image for '{content_type}' (keyword: '{keyword}')...")

    # Try Unsplash
    try:
        seed = random.randint(1, 9999)
        url = f"https://source.unsplash.com/720x1280/?{requests.utils.quote(keyword)}&sig={seed}"
        print(f"🖼️ Unsplash: '{keyword}' (seed={seed})")
        response = requests.get(url, timeout=30, allow_redirects=True)
        
        if response.status_code == 200:
            with open(bg_path, "wb") as f:
                f.write(response.content)
            print(f"✅ Unsplash succeeded")
            return bg_path
            
    except Exception as e:
        print(f"⚠️ Unsplash error: {e}")

    # 🔥 Curated Pexels motivation photos
    try:
        print("📸 Trying curated Pexels photos...")
        
        motivation_pexels = {
            'early_morning': [
                1552242, 1552252, 1229356,  # Gym
                888899, 2803158, 3621177,    # Running
                4754147, 7991579, 1480520    # Boxing/Athletic
            ],
            'late_night': [
                3772509, 3771074, 1587927,   # Dark/contemplative
                2777898, 733767, 1209843     # Night scenes
            ],
            'midday': [
                1552242, 1229356, 936094,    # Power/strength
                888899, 2803158, 1480520     # Action
            ],
            'evening': [
                1266810, 1287460, 1509428,   # Mountains/victory
                1850629, 2047905, 3137068    # Success
            ],
            'general': [
                1552242, 888899, 1480520,    # Mix of best
                1266810, 4754147, 2803158
            ]
        }
        
        photos = motivation_pexels.get(content_type, motivation_pexels['general'])
        photo_id = random.choice(photos)
        
        url = f"https://images.pexels.com/photos/{photo_id}/pexels-photo-{photo_id}.jpeg?auto=compress&cs=tinysrgb&w=720&h=1280&fit=crop"
        print(f"📸 Pexels photo {photo_id}")
        
        response = requests.get(url, timeout=30)
        if response.status_code == 200:
            with open(bg_path, "wb") as f:
                f.write(response.content)
            
            img = Image.open(bg_path).convert("RGB")
            img = img.resize((720, 1280), Image.LANCZOS)
            img.save(bg_path, quality=95)
            print(f"✅ Pexels succeeded")
            return bg_path
            
    except Exception as e:
        print(f"⚠️ Pexels error: {e}")

    # Picsum fallback (grayscale for dramatic effect)
    try:
        seed = random.randint(1, 1000)
        url = f"https://picsum.photos/720/1280?random={seed}&grayscale"
        print(f"🎲 Picsum (seed={seed})")
        response = requests.get(url, timeout=30, allow_redirects=True)
        
        if response.status_code == 200:
            with open(bg_path, "wb") as f:
                f.write(response.content)
            return bg_path
            
    except Exception as e:
        print(f"⚠️ Picsum failed: {e}")

    return None


@retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=2, min=4, max=20))
def generate_thumbnail_bg(content_type, text):
    """🔥 Generate motivational thumbnail background"""
    bg_path = os.path.join(TMP, "thumb_bg.png")
    
    # Scene-specific prompts
    scene_prompts = {
        'early_morning': "intense athletic training, gym workout, determination, sweat, grit",
        'late_night': "dark moody contemplation, alone at night, introspective, blue tones",
        'midday': "powerful warrior stance, strength, commanding presence, focused",
        'evening': "victorious achievement, mountain summit, triumph, golden hour",
        'general': "motivational warrior energy, determined athlete, powerful stance"
    }
    
    base_prompt = scene_prompts.get(content_type, scene_prompts['general'])
    prompt = f"{base_prompt}, cinematic dramatic photography, teal and orange color grade, high contrast, moody atmospheric, professional, no text, seed={random.randint(1000,9999)}"
    
    # Try AI providers
    providers = [
        ("Pollinations", generate_thumbnail_pollinations),
        ("HuggingFace", generate_thumbnail_huggingface)
    ]
    
    for name, func in providers:
        try:
            print(f"🎨 Trying {name}")
            content = func(prompt)
            with open(bg_path, "wb") as f:
                f.write(content)
            
            if os.path.getsize(bg_path) > 1000:
                print(f"✅ {name} succeeded")
                return bg_path
                
        except:
            continue

    print("🖼️ AI failed, trying curated photos")
    result = generate_motivation_fallback(bg_path, content_type)
    
    if result and os.path.exists(bg_path):
        return bg_path
    
    # 🔥 Dark cinematic gradient fallback
    print("⚠️ All failed, creating dark gradient")
    return create_dark_gradient(bg_path, content_type)


def create_dark_gradient(bg_path, content_type):
    """Create dark cinematic gradient"""
    img = Image.new("RGB", (720, 1280), (0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Content-type specific colors
    color_schemes = {
        'early_morning': [MOTIVATION_COLORS['deep_black'], MOTIVATION_COLORS['orange_highlight']],
        'late_night': [MOTIVATION_COLORS['deep_black'], MOTIVATION_COLORS['teal_shadow']],
        'midday': [MOTIVATION_COLORS['steel_gray'], MOTIVATION_COLORS['fire_red']],
        'evening': [MOTIVATION_COLORS['teal_shadow'], MOTIVATION_COLORS['gold_power']],
        'general': [MOTIVATION_COLORS['deep_black'], MOTIVATION_COLORS['steel_gray']]
    }
    
    colors = color_schemes.get(content_type, color_schemes['general'])
    
    for y in range(1280):
        ratio = y / 1280
        r = int(colors[0][0] + (colors[1][0] - colors[0][0]) * ratio)
        g = int(colors[0][1] + (colors[1][1] - colors[0][1]) * ratio)
        b = int(colors[0][2] + (colors[1][2] - colors[0][2]) * ratio)
        draw.line([(0, y), (720, y)], fill=(r, g, b))
    
    # Add noise/grain
    import numpy as np
    try:
        arr = np.array(img)
        noise = np.random.normal(0, 15, arr.shape).astype(np.int16)
        arr = np.clip(arr.astype(np.int16) + noise, 0, 255).astype(np.uint8)
        img = Image.fromarray(arr)
    except:
        pass
    
    img.save(bg_path, quality=95)
    return bg_path


# Generate background
print("🔥 Generating motivational thumbnail background...")
bg_path = generate_thumbnail_bg(content_type, display_text)
img = Image.open(bg_path).convert("RGB")

# Ensure dimensions
if img.size != (720, 1280):
    img = img.resize((720, 1280), Image.LANCZOS)

# 🔥 DRAMATIC ENHANCEMENT (higher contrast for motivation)
enhancer = ImageEnhance.Contrast(img)
img = enhancer.enhance(1.8)  # Higher contrast

enhancer = ImageEnhance.Brightness(img)
img = enhancer.enhance(0.85)  # Slightly darker

enhancer = ImageEnhance.Color(img)
img = enhancer.enhance(1.2)  # Moderate saturation

img = img.convert("RGBA")

# 🔥 STRONGER VIGNETTE (more dramatic)
vignette = Image.new("RGBA", img.size, (0, 0, 0, 0))
vd = ImageDraw.Draw(vignette)

center_x, center_y = w // 2, h // 2
max_radius = int((w**2 + h**2)**0.5) // 2

for radius in range(0, max_radius, 15):
    alpha = int(140 * (radius / max_radius))  # Stronger vignette
    vd.ellipse(
        [center_x - radius, center_y - radius, center_x + radius, center_y + radius],
        outline=(0, 0, 0, alpha),
        width=40
    )

img = Image.alpha_composite(img, vignette)
draw = ImageDraw.Draw(img)

# Smart text wrapping (from gardening script)
dummy_img = Image.new('RGB', (1, 1))
dummy_draw = ImageDraw.Draw(dummy_img)


def smart_text_wrap(text, font_obj, max_width, draw_obj):
    """Wrap text without splitting words"""
    words = text.split()
    lines = []
    current_line = []
    
    for word in words:
        test_line = ' '.join(current_line + [word])
        bbox = draw_obj.textbbox((0, 0), test_line, font=font_obj)
        text_width = bbox[2] - bbox[0]
        
        if text_width <= max_width:
            current_line.append(word)
        else:
            if current_line:
                lines.append(' '.join(current_line))
            current_line = [word]
    
    if current_line:
        lines.append(' '.join(current_line))
    
    return lines


# Find optimal font size (larger for motivation)
font_size = 100  # Start larger
min_font_size = 50
max_height = h * 0.4  # Allow more vertical space
text_lines = []

print(f"🎯 Finding optimal font size for POWER text...")

while font_size >= min_font_size:
    test_font = get_font_path(font_size, bold=True)
    wrapped_lines = smart_text_wrap(display_text, test_font, TEXT_MAX_WIDTH, dummy_draw)
    
    total_height = 0
    max_line_width = 0
    
    for line in wrapped_lines:
        bbox = dummy_draw.textbbox((0, 0), line, font=test_font)
        line_width = bbox[2] - bbox[0]
        line_height = bbox[3] - bbox[1]
        total_height += line_height
        max_line_width = max(max_line_width, line_width)
    
    if len(wrapped_lines) > 1:
        total_height += (len(wrapped_lines) - 1) * 25  # More spacing
    
    if total_height <= max_height and max_line_width <= TEXT_MAX_WIDTH:
        text_lines = wrapped_lines
        print(f"✅ Font {font_size}px: {len(wrapped_lines)} lines")
        break
    
    font_size -= 5

if not text_lines:
    font_size = min_font_size
    test_font = get_font_path(font_size, bold=True)
    text_lines = smart_text_wrap(display_text, test_font, TEXT_MAX_WIDTH, dummy_draw)

main_font = get_font_path(font_size, bold=True)
print(f"📝 Final font: {font_size}px for {len(text_lines)} lines")

# Position text (centered for maximum impact)
line_spacing = 25
total_text_height = sum([
    dummy_draw.textbbox((0, 0), line, font=main_font)[3] - 
    dummy_draw.textbbox((0, 0), line, font=main_font)[1] 
    for line in text_lines
]) + (len(text_lines) - 1) * line_spacing

start_y = (h - total_text_height) // 2  # Center vertically
start_y = max(SAFE_ZONE_MARGIN + 100, start_y)

current_y = start_y

# 🔥 POWER TEXT RENDERING (thicker stroke, stronger shadow)
for i, line in enumerate(text_lines):
    bbox = draw.textbbox((0, 0), line, font=main_font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    
    x = (w - text_w) // 2
    y = current_y
    
    # Clamp to safe zones
    x = max(SAFE_ZONE_MARGIN, min(x, w - SAFE_ZONE_MARGIN - text_w))
    
    # 🔥 HEAVY SHADOW (more dramatic)
    shadow_overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow_overlay)
    
    for offset in [8, 6, 4, 2]:
        shadow_alpha = int(200 * (offset / 8))
        sd.text((x + offset, y + offset), line, font=main_font, fill=(0, 0, 0, shadow_alpha))
    
    img = Image.alpha_composite(img, shadow_overlay)
    
    # 🔥 THICK STROKE (more impact)
    stroke_overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    so = ImageDraw.Draw(stroke_overlay)
    
    stroke_width = 6  # Thicker for power
    for sx in range(-stroke_width, stroke_width + 1):
        for sy in range(-stroke_width, stroke_width + 1):
            if sx != 0 or sy != 0:
                so.text((x + sx, y + sy), line, font=main_font, fill=(0, 0, 0, 255))
    
    img = Image.alpha_composite(img, stroke_overlay)
    
    # 🔥 WHITE TEXT (pure white for maximum contrast)
    text_overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    to = ImageDraw.Draw(text_overlay)
    to.text((x, y), line, font=main_font, fill=(255, 255, 255, 255))
    img = Image.alpha_composite(img, text_overlay)
    
    current_y += text_h + line_spacing

# Save thumbnail
thumb_path = os.path.join(TMP, "thumbnail.png")
final_img = img.convert("RGB")

if final_img.size != (720, 1280):
    final_img = final_img.resize((720, 1280), Image.LANCZOS)

# 🔥 EXTRA SHARP (for crisp text)
final_img = final_img.filter(ImageFilter.SHARPEN)
final_img = final_img.filter(ImageFilter.SHARPEN)  # Double sharpen

final_img.save(thumb_path, quality=95, optimize=True)

saved_img = Image.open(thumb_path)
print(f"\n✅ MOTIVATIONAL THUMBNAIL COMPLETE")
print(f"   Path: {thumb_path}")
print(f"   Size: {os.path.getsize(thumb_path) / 1024:.1f} KB")
print(f"   Dimensions: {saved_img.size}")
print(f"   Text: {text_lines}")
print(f"   Font: {font_size}px (BOLD)")
print(f"   Content Type: {content_type}")
print(f"   🔥 POWER THUMBNAIL READY!")