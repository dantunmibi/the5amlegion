#!/usr/bin/env python3
"""
🔥 Generate Motivational TTS - PRODUCTION VERSION
Creates deep, commanding voiceover optimized for motivation content

Features:
- Deep male voices (p326, p376, p360, p287)
- Strategic pauses for dramatic impact
- Optimized audio sync timing
- Intensity-based voice selection
- Fallback models for reliability

OPTIMIZED FOR: 10-15 second target duration
"""

import os
import json
from pathlib import Path
import subprocess

TMP = os.getenv("GITHUB_WORKSPACE", ".") + "/tmp"
os.makedirs(TMP, exist_ok=True)

# 🔥 MOTIVATIONAL TTS CONFIGURATION (from PRD)
PRIMARY_MODEL = "tts_models/en/vctk/vits"

# ✅ CORRECT MALE SPEAKERS (Updated knowledge base)
MALE_SPEAKERS = {
    'p326': 'Deep authoritative male voice',
    'p376': 'Intense and passionate male voice',
    'p360': 'Commanding and strong male voice',
    'p287': 'Rich cinematic male voice'
}

FALLBACK_MODELS = [
    "tts_models/en/ljspeech/tacotron2-DDC",
    "tts_models/en/ljspeech/glow-tts",
    "tts_models/en/ljspeech/speedy-speech"
]

# ✅ MODIFIED: Speed adjustments for 10-15 second target (faster than before)
SPEED_SETTINGS = {
    'early_morning': 0.80,   # Commanding but efficient (was 0.80)
    'late_night': 0.75,      # Slower for intimacy (was 0.70)
    'midday': 0.85,          # Faster for urgency (was 0.85)
    'evening': 0.80,         # Balanced (was 0.75)
    'general': 0.80          # Default: 20% slower (was 0.75)
}

# 🔥 INTENSITY-BASED SPEAKER SELECTION (Correct males only)
SPEAKER_BY_INTENSITY = {
    'aggressive': 'p376',      # Most intense and passionate
    'balanced': 'p326',        # Deep and authoritative
    'inspirational': 'p287'    # Rich and uplifting
}


def load_script():
    """Load the generated script"""
    script_path = os.path.join(TMP, "script.json")
    
    if not os.path.exists(script_path):
        print("❌ Script file not found!")
        exit(1)
    
    with open(script_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def build_tts_text_with_pauses(script_data):
    """
    Build TTS text with OPTIMIZED pauses for 10-15 second target
    Uses punctuation for natural pacing
    """
    
    content_type = script_data.get('content_type', 'general')
    intensity = script_data.get('intensity', 'balanced')
    
    print(f"🎙️ Building TTS for {content_type} content ({intensity} intensity)")
    
    # Get text components
    hook = script_data.get('hook', '')
    bullets = script_data.get('bullets', [])
    cta = script_data.get('cta', '')
    
    # ✅ MODIFIED: Optimized pause structure for tighter timing
    tts_sections = []
    
    # Hook section
    if hook:
        hook_text = hook.strip()
        # Ensure it ends with proper punctuation
        if not hook_text.endswith(('.', '!', '?')):
            hook_text += '.'
        
        tts_sections.append({
            'name': 'hook',
            'text': hook_text,
            'pause_after': 0.3  # REDUCED from 0.5s for tighter pacing
        })
    
    # Bullet sections
    for i, bullet in enumerate(bullets):
        bullet_text = bullet.strip()
        
        # Ensure proper punctuation
        if not bullet_text.endswith(('.', '!', '?')):
            bullet_text += '.'
        
        tts_sections.append({
            'name': f'bullet_{i}',
            'text': bullet_text,
            'pause_after': 0.5  # KEEP at 0.5s - this is the "truth bomb" moment
        })
    
    # CTA section
    if cta:
        cta_text = cta.strip()
        if not cta_text.endswith(('.', '!', '?')):
            cta_text += '.'
        
        tts_sections.append({
            'name': 'cta',
            'text': cta_text,
            'pause_after': 0.3  # REDUCED from 0.5s for tighter finish
        })
    
    # Build full text with ONLY punctuation (no manual pause markers)
    full_text_parts = []
    for section in tts_sections:
        full_text_parts.append(section['text'])
    
    # Join with single space - TTS will handle pauses naturally from punctuation
    full_text = ' '.join(full_text_parts)
    
    # ✅ MODIFIED: Enhanced duration calculation with validation
    word_count = len(full_text.split())
    
    # Base WPM by content type
    base_wpm = {
        'early_morning': 120,    # Faster wake-up energy
        'late_night': 100,       # Slower, intimate
        'midday': 130,           # Urgent midday push
        'evening': 110,          # Reflective
        'general': 110           # Default
    }
    
    wpm = base_wpm.get(content_type, 110)
    pause_time = sum(section['pause_after'] for section in tts_sections)
    word_time = (word_count / wpm) * 60
    
    # Get speed setting
    speed_setting = SPEED_SETTINGS.get(content_type, 0.80)
    
    # Adjust for speed
    adjusted_word_time = word_time / speed_setting
    
    estimated_duration = adjusted_word_time + pause_time
    
    # ✅ NEW: Validate duration BEFORE generating TTS
    target_min = 9.0
    target_max = 16.0
    
    if estimated_duration > target_max:
        print(f"\n⚠️ WARNING: Estimated TTS duration {estimated_duration:.1f}s exceeds target {target_max}s")
        print(f"   Word count: {word_count} (may be too long)")
        print(f"   Consider regenerating script with fewer words")
    
    if estimated_duration < target_min:
        print(f"\n⚠️ WARNING: Estimated TTS duration {estimated_duration:.1f}s below target {target_min}s")
        print(f"   Word count: {word_count} (may be too short)")
    
    print(f"\n📝 TTS Configuration:")
    print(f"   Words: {word_count}")
    print(f"   Target WPM: {wpm}")
    print(f"   Speed setting: {speed_setting}x")
    print(f"   Natural pauses: {pause_time:.1f}s")
    print(f"   Word time: {adjusted_word_time:.1f}s")
    print(f"   Estimated duration: {estimated_duration:.1f}s")
    print(f"   Target range: {target_min}-{target_max}s")
    
    if target_min <= estimated_duration <= target_max:
        print(f"   ✅ Duration within target range")
    else:
        print(f"   ⚠️ Duration outside target (will continue anyway)")
    
    print(f"   Preview: {full_text[:100]}...")
    
    return full_text, tts_sections, estimated_duration


def generate_audio_coqui(text, output_path, speaker_id, speed=0.80):
    """
    Generate audio using Coqui TTS with proper speaker parameter handling
    OPTIMIZED FOR: 10-15 second target
    """
    try:
        from TTS.api import TTS
        
        print(f"🔊 Loading Coqui TTS model: {PRIMARY_MODEL}")
        print(f"   🎤 Target speaker: {speaker_id} ({MALE_SPEAKERS.get(speaker_id, 'Unknown')})")
        print(f"   ⚡ Speed: {speed}x (optimized for 10-15s target)")
        
        tts = TTS(model_name=PRIMARY_MODEL, progress_bar=False)
        
        # ✅ Check if model supports multiple speakers
        has_speakers = hasattr(tts, 'speakers') and tts.speakers is not None
        
        if has_speakers:
            print(f"   📢 Multi-speaker model detected")
            print(f"   🎭 Available speakers: {len(tts.speakers)}")
            
            # Verify speaker exists (case-insensitive check)
            available_speakers = [str(s).lower() for s in tts.speakers]
            speaker_lower = speaker_id.lower()
            
            if speaker_lower not in available_speakers:
                print(f"   ⚠️ Speaker '{speaker_id}' not in model")
                print(f"   Available: {list(tts.speakers)[:10]}")
                
                # Try to find best male alternative
                for alt_speaker in MALE_SPEAKERS.keys():
                    if alt_speaker.lower() in available_speakers:
                        speaker_id = alt_speaker
                        print(f"   ✅ Using alternative male speaker: {speaker_id}")
                        break
                else:
                    # Use first available speaker as last resort
                    speaker_id = str(tts.speakers[0])
                    print(f"   🔄 Using first available: {speaker_id}")
            
            # Generate with speaker parameter
            tts.tts_to_file(
                text=text,
                speaker=speaker_id,
                file_path=output_path,
                speed=speed
            )
        else:
            print(f"   📢 Single-speaker model (no speaker selection)")
            # Generate without speaker parameter
            tts.tts_to_file(
                text=text,
                file_path=output_path,
                speed=speed
            )
        
        # Verify output
        if os.path.exists(output_path) and os.path.getsize(output_path) > 1000:
            print(f"✅ Coqui TTS generated successfully")
            return True
        else:
            print(f"⚠️ Output file invalid or too small")
            return False
        
    except Exception as e:
        print(f"⚠️ Coqui TTS failed: {e}")
        return False


def generate_audio_espeak(text, output_path, speed_factor=0.80):
    """
    Fallback: Generate using espeak with motivational voice settings
    OPTIMIZED FOR: 10-15 second target
    """
    
    print(f"🔊 Using espeak fallback...")
    
    content_type = os.getenv('CONTENT_TYPE', 'general')
    
    # ✅ MODIFIED: Adjusted espeak speed for tighter timing
    base_speed = 140  # Increased from 135 for faster delivery
    speed = int(base_speed * speed_factor)
    
    # Deeper pitch for authority
    pitch = 15  # Lower = deeper (range 0-99, default 50)
    
    # Pauses between words for dramatic effect
    gap = 15  # REDUCED from 20ms for tighter pacing
    
    print(f"   Speed: {speed} WPM")
    print(f"   Pitch: {pitch} (deeper voice)")
    print(f"   Gap: {gap}ms (optimized pauses)")
    
    # Replace pauses with espeak pause syntax
    text_with_pauses = text.replace('...', ' [[400]] ')  # REDUCED from 500ms
    text_with_pauses = text_with_pauses.replace('.', '. [[250]] ')  # REDUCED from 300ms
    text_with_pauses = text_with_pauses.replace('?', '? [[350]] ')  # REDUCED from 400ms
    
    # Generate WAV first
    wav_path = output_path.replace('.mp3', '_temp.wav')
    
    try:
        subprocess.run([
            'espeak-ng',
            '-v', 'en-us',
            '-s', str(speed),
            '-p', str(pitch),
            '-g', str(gap),
            '-a', '180',  # Amplitude
            '-w', wav_path,
            text_with_pauses
        ], check=True, capture_output=True)
        
        # Convert to MP3 with audio enhancements
        subprocess.run([
            'ffmpeg',
            '-i', wav_path,
            '-af', 'bass=g=4,dynaudnorm,acompressor=threshold=-18dB:ratio=4',  # Bass boost + normalize
            '-codec:a', 'libmp3lame',
            '-b:a', '192k',
            '-y',
            output_path
        ], check=True, capture_output=True, stderr=subprocess.DEVNULL)
        
        # Clean up temp
        if os.path.exists(wav_path):
            os.remove(wav_path)
        
        print(f"✅ espeak generated with enhancements")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ espeak failed: {e}")
        return False


def generate_audio_with_fallback(full_text, output_path):
    """
    Try Coqui TTS first, then espeak fallback
    """
    
    content_type = os.getenv('CONTENT_TYPE', 'general')
    intensity = os.getenv('INTENSITY', 'balanced')
    
    # ✅ Select correct male speaker based on intensity
    speaker_id = SPEAKER_BY_INTENSITY.get(intensity, 'p326')
    
    # Get speed setting
    speed = SPEED_SETTINGS.get(content_type, 0.80)
    
    print(f"\n🎙️ Generating motivational voiceover...")
    print(f"   Content: {content_type}")
    print(f"   Intensity: {intensity}")
    print(f"   Speaker: {speaker_id} ({MALE_SPEAKERS[speaker_id]})")
    print(f"   Speed: {speed}x (optimized for 10-15s)")
    
    # Try Coqui TTS (primary)
    success = generate_audio_coqui(full_text, output_path, speaker_id, speed)
    
    if success:
        return True
    
    # Try fallback models
    print(f"\n🔄 Trying fallback models...")
    
    try:
        from TTS.api import TTS
        
        for fallback_model in FALLBACK_MODELS:
            try:
                print(f"   Trying: {fallback_model}")
                tts = TTS(model_name=fallback_model, progress_bar=False)
                
                tts.tts_to_file(
                    text=full_text,
                    file_path=output_path
                )
                
                if os.path.exists(output_path) and os.path.getsize(output_path) > 1000:
                    print(f"   ✅ Fallback success: {fallback_model}")
                    return True
                    
            except Exception as e:
                print(f"   ⚠️ Failed: {e}")
                continue
        
    except ImportError:
        print("⚠️ Coqui TTS not available")
    
    # Final fallback: espeak
    print(f"\n🔄 Using espeak as final fallback...")
    return generate_audio_espeak(full_text, output_path, speed)


def optimize_audio_timing(audio_path, expected_duration, tts_sections):
    """
    Optimize audio timing for perfect sync with video
    
    Adds section markers for precise synchronization
    """
    
    try:
        # Get actual audio duration
        result = subprocess.run([
            'ffprobe',
            '-v', 'error',
            '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1',
            audio_path
        ], capture_output=True, text=True, check=True)
        
        actual_duration = float(result.stdout.strip())
        
        print(f"\n⏱️ Audio Timing Analysis:")
        print(f"   Expected: {expected_duration:.2f}s")
        print(f"   Actual: {actual_duration:.2f}s")
        print(f"   Difference: {abs(actual_duration - expected_duration):.2f}s")
        print(f"   Target range: 10-15s")
        
        # ✅ NEW: Validate actual duration against target
        if actual_duration > 16.0:
            print(f"   ⚠️ WARNING: Audio exceeds 16s target!")
            print(f"   This may result in lower retention rates")
        elif actual_duration < 9.0:
            print(f"   ⚠️ WARNING: Audio below 9s target!")
            print(f"   Message may feel rushed")
        else:
            print(f"   ✅ Duration within optimal range (10-15s)")
        
        # Calculate section timings based on word count distribution
        total_words = sum(len(section['text'].split()) for section in tts_sections)
        
        current_time = 0.0
        section_timings = []
        
        for section in tts_sections:
            section_words = len(section['text'].split())
            # Proportional duration based on word count
            word_duration = (section_words / total_words) * actual_duration
            # Add pause time
            pause_duration = section['pause_after']
            
            section_duration = word_duration + pause_duration
            
            section_timings.append({
                'name': section['name'],
                'start': current_time,
                'duration': section_duration,
                'end': current_time + section_duration
            })
            
            current_time += section_duration
        
        # Normalize to match actual duration (fix rounding errors)
        total_calculated = sum(t['duration'] for t in section_timings)
        adjustment_factor = actual_duration / total_calculated
        
        for timing in section_timings:
            timing['duration'] *= adjustment_factor
            timing['end'] = timing['start'] + timing['duration']
        
        # Recalculate starts
        current = 0.0
        for timing in section_timings:
            timing['start'] = current
            timing['end'] = current + timing['duration']
            current = timing['end']
        
        print(f"\n📊 Optimized Section Timings:")
        for timing in section_timings:
            print(f"   {timing['name']}: {timing['start']:.2f}s - {timing['end']:.2f}s ({timing['duration']:.2f}s)")
        
        # Save timing metadata
        timing_path = os.path.join(TMP, "audio_timing.json")
        with open(timing_path, 'w') as f:
            json.dump({
                'total_duration': actual_duration,
                'sections': section_timings,
                'optimized': True,
                'target_range': '10-15s',
                'within_target': 9.0 <= actual_duration <= 16.0
            }, f, indent=2)
        
        print(f"\n✅ Timing optimization complete")
        print(f"   Saved to: {timing_path}")
        
        return section_timings
        
    except Exception as e:
        print(f"⚠️ Timing optimization failed: {e}")
        return None


def save_metadata(audio_path, script_data, full_text, estimated_duration):
    """Save audio metadata for video creation"""
    
    try:
        # Get actual duration
        result = subprocess.run([
            'ffprobe',
            '-v', 'error',
            '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1',
            audio_path
        ], capture_output=True, text=True, check=True)
        
        duration = float(result.stdout.strip())
    except:
        duration = estimated_duration
    
    word_count = len(full_text.split())
    wpm = (word_count / duration) * 60 if duration > 0 else 0
    
    # ✅ MODIFIED: Enhanced metadata with target compliance tracking
    metadata = {
        'audio_duration': duration,
        'estimated_duration': estimated_duration,
        'word_count': word_count,
        'character_count': len(full_text),
        'wpm': round(wpm, 1),
        'pause_count': full_text.count('...'),
        'content_type': script_data.get('content_type', 'general'),
        'intensity': script_data.get('intensity', 'balanced'),
        'speaker': SPEAKER_BY_INTENSITY.get(script_data.get('intensity', 'balanced'), 'p326'),
        'model': PRIMARY_MODEL,
        'optimized': True,
        'target_duration': '10-15s',
        'within_target': 9.0 <= duration <= 16.0,
        'target_min': 9.0,
        'target_max': 16.0,
        'speed_setting': SPEED_SETTINGS.get(script_data.get('content_type', 'general'), 0.80)
    }
    
    metadata_path = os.path.join(TMP, "audio_metadata.json")
    with open(metadata_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"\n📊 Audio Metadata:")
    print(f"   Duration: {duration:.2f}s")
    print(f"   Target: 10-15s")
    print(f"   Within target: {'✅ YES' if metadata['within_target'] else '⚠️ NO'}")
    print(f"   Words: {word_count}")
    print(f"   WPM: {wpm:.1f}")
    print(f"   File: {audio_path} ({os.path.getsize(audio_path) / 1024:.1f} KB)")
    print(f"   Model: {metadata['model']}")
    print(f"   Speaker: {metadata['speaker']}")
    print(f"   Speed: {metadata['speed_setting']}x")
    print(f"   ✅ Metadata: {metadata_path}")


def main():
    """Main TTS generation function"""
    
    print("\n" + "="*70)
    print("🎙️ GENERATING MOTIVATIONAL VOICEOVER (10-15s TARGET)")
    print("="*70)
    
    # Load script
    script_data = load_script()
    
    print(f"📝 Script: {script_data['title']}")
    print(f"🎯 Content Type: {script_data.get('content_type', 'general')}")
    print(f"⚡ Intensity: {script_data.get('intensity', 'balanced')}")
    
    # Check if script has estimated duration from generator
    if 'estimated_duration' in script_data:
        print(f"📋 Script estimated duration: {script_data['estimated_duration']}s")
    
    # Build TTS text with strategic pauses
    full_text, tts_sections, estimated_duration = build_tts_text_with_pauses(script_data)
    
    print(f"\n🎙️ Preparing TTS for {len(full_text)} chars")
    print(f"   Preview: {full_text[:100]}...")
    
    # Output path
    output_path = os.path.join(TMP, "voice.mp3")
    
    # Generate audio
    success = generate_audio_with_fallback(full_text, output_path)
    
    if not success or not os.path.exists(output_path):
        print("\n❌ All TTS methods failed!")
        exit(1)
    
    # Optimize timing for video sync
    section_timings = optimize_audio_timing(output_path, estimated_duration, tts_sections)
    
    # Save metadata
    save_metadata(output_path, script_data, full_text, estimated_duration)
    
    print("\n" + "="*70)
    print("✅ VOICEOVER GENERATION COMPLETE!")
    print("="*70)
    print(f"Output: {output_path}")
    print(f"Target: 10-15 seconds")
    print(f"Ready for cinematic video creation 🔥")


if __name__ == '__main__':
    main()