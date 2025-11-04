#!/usr/bin/env python3
"""
🔥 Generate Motivational Script - SCHEDULER-INTEGRATED VERSION
Creates emotionally charged motivational scripts using:
- Scheduler data (pillar, tone, keywords)
- Trending topics (real-time viral content)
- Content history (avoid duplicates)
- Retry logic with exponential backoff
- Robust JSON parsing

OPTIMIZED FOR: 10-15 second YouTube Shorts (maximum retention)
"""

import os
import json
import re
import hashlib
from datetime import datetime
import google.generativeai as genai
from tenacity import retry, stop_after_attempt, wait_exponential

TMP = os.getenv("GITHUB_WORKSPACE", ".") + "/tmp"
os.makedirs(TMP, exist_ok=True)
HISTORY_FILE = os.path.join(TMP, "content_history.json")
SCHEDULER_FILE = os.path.join(TMP, "posting_schedule.json")

# Configure Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

try:
    models = genai.list_models()
    model_name = None
    for m in models:
        if 'generateContent' in m.supported_generation_methods:
            if '2.0-flash' in m.name or '2.5-flash' in m.name:
                model_name = m.name
                break
            elif '1.5-flash' in m.name and not model_name:
                model_name = m.name
    
    if not model_name:
        model_name = "models/gemini-1.5-flash"
    
    print(f"✅ Using model: {model_name}")
    model = genai.GenerativeModel(model_name)
except Exception as e:
    print(f"⚠️ Error listing models: {e}")
    model = genai.GenerativeModel("models/gemini-1.5-flash")


def load_scheduler_data():
    """Load data from optimal scheduler"""
    if os.path.exists(SCHEDULER_FILE):
        try:
            with open(SCHEDULER_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                print(f"✅ Loaded scheduler data")
                return data
        except Exception as e:
            print(f"⚠️ Could not load scheduler data: {e}")
            return None
    return None


def load_history():
    """Load content history from previous runs"""
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                history = json.load(f)
                print(f"📂 Loaded {len(history.get('topics', []))} topics from history")
                return history
        except Exception as e:
            print(f"⚠️ Could not load history: {e}")
            return {'topics': [], 'version': '2.0'}
    
    print("📂 No previous history found, starting fresh")
    return {'topics': [], 'version': '2.0'}


def save_to_history(topic, script_hash, title, script_data):
    """Save generated content to history"""
    history = load_history()
    
    history['topics'].append({
        'topic': topic,
        'title': title,
        'hash': script_hash,
        'hook': script_data.get('hook', ''),
        'key_phrase': script_data.get('key_phrase', ''),
        'content_type': script_data.get('content_type', 'general'),
        'priority': script_data.get('priority', 'medium'),
        'date': datetime.now().isoformat(),
        'timestamp': datetime.now().timestamp()
    })
    
    # Keep last 100 topics
    history['topics'] = history['topics'][-100:]
    history['last_updated'] = datetime.now().isoformat()
    history['version'] = '2.0'
    
    with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(history, f, indent=2, ensure_ascii=False)
    
    print(f"💾 Saved to history ({len(history['topics'])} total topics)")


def get_content_hash(data):
    """Generate hash of content to detect exact duplicates"""
    content_str = f"{data.get('title', '')}{data.get('hook', '')}{data.get('bullets', [])}"
    return hashlib.md5(content_str.encode()).hexdigest()


def load_trending():
    """Load trending topics from fetch_trending.py"""
    trending_file = os.path.join(TMP, "trending.json")
    if os.path.exists(trending_file):
        try:
            with open(trending_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️ Could not load trending data: {e}")
            return None
    return None


def is_similar_topic(new_title, previous_titles, similarity_threshold=0.6):
    """Check if topic is too similar to previous ones with time decay"""
    new_words = set(new_title.lower().split())
    
    for idx, prev_title in enumerate(reversed(previous_titles[-30:])):
        prev_words = set(prev_title.lower().split())
        
        intersection = len(new_words & prev_words)
        union = len(new_words | prev_words)
        
        if union > 0:
            base_similarity = intersection / union
            decay_factor = 1.0 / (1.0 + idx * 0.05)
            adjusted_threshold = similarity_threshold * decay_factor
            
            if base_similarity > adjusted_threshold:
                print(f"⚠️ Topic too similar ({base_similarity:.2f} > {adjusted_threshold:.2f})")
                print(f"   To: {prev_title}")
                return True
    
    return False


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def generate_script_with_retry(prompt):
    """Generate script with automatic retry on failure"""
    response = model.generate_content(prompt)
    return response.text.strip()


def validate_script_uses_trending_topic(script_data, trending_topics):
    """Validate that script actually uses one of the trending topics"""
    if not trending_topics:
        return True
    
    script_text = f"{script_data['title']} {script_data['hook']} {' '.join(script_data.get('bullets', []))}".lower()
    
    trend_keywords = []
    for topic in trending_topics:
        words = [w for w in topic.lower().split() if len(w) > 4 and w not in {
            'this', 'that', 'with', 'from', 'will', 'just', 'your', 'they',
            'them', 'what', 'when', 'where', 'which', 'while', 'about',
            'have', 'been', 'were', 'their', 'there', 'these', 'those',
            'make', 'made', 'take', 'took', 'very', 'more', 'most', 'some',
            'other', 'into', 'than', 'then', 'here'
        }]
        trend_keywords.extend(words)
    
    trend_keywords = list(set(trend_keywords))
    matches = sum(1 for kw in trend_keywords if kw in script_text)
    
    if matches < 2:
        print(f"⚠️ Script doesn't use trending topics! Only {matches} matches.")
        return False
    
    print(f"✅ Script uses trending topics ({matches} keyword matches)")
    return True


def validate_script_data(data):
    """
    Validate generated script has all required fields for 3-act structure
    OPTIMIZED FOR: 10-15 second target duration
    """
    required_fields = ["title", "hook", "bullets", "cta"]
    
    for field in required_fields:
        if field not in data or not data[field]:
            raise ValueError(f"Missing or empty required field: {field}")
    
    if not isinstance(data["bullets"], list) or len(data["bullets"]) != 1:
        raise ValueError("'bullets' must be a list containing exactly one item for Act 2.")
    
    if not data["bullets"][0] or len(data["bullets"][0]) < 5:
        raise ValueError("The bullet for Act 2 is too short or empty.")
    
    # ✅ MODIFIED: Stricter word count validation for 10-15 second target
    hook_words = len(data["hook"].split())
    truth_words = len(data["bullets"][0].split())
    cta_words = len(data["cta"].split())
    total_words = hook_words + truth_words + cta_words
    
    if total_words > 30:
        raise ValueError(f"Script too long: {total_words} words (max 30 for 10-15 second target)")
    
    if hook_words > 8:
        print(f"⚠️ Hook too long ({hook_words} words), shortening...")
        words = data["hook"].split()[:8]
        data["hook"] = " ".join(words)
    
    if truth_words > 15:
        print(f"⚠️ Truth too long ({truth_words} words), shortening...")
        words = data["bullets"][0].split()[:15]
        data["bullets"][0] = " ".join(words)
    
    if cta_words > 7:
        print(f"⚠️ CTA too long ({cta_words} words), shortening...")
        words = data["cta"].split()[:7]
        data["cta"] = " ".join(words)
    
    if len(data["title"]) > 70:
        print(f"⚠️ Title too long ({len(data['title'])} chars), truncating...")
        data["title"] = data["title"][:67] + "..."
        
    return True


def estimate_script_duration(script_data, speaking_rate=0.80, base_wpm=110):
    """
    Estimate final video duration for validation
    
    Args:
        script_data: Script dictionary with hook, bullets, cta
        speaking_rate: TTS speed multiplier (0.80 = 20% slower)
        base_wpm: Base words per minute
    
    Returns:
        Estimated duration in seconds
    """
    hook_words = len(script_data.get('hook', '').split())
    truth_words = len(script_data['bullets'][0].split()) if script_data.get('bullets') else 0
    cta_words = len(script_data.get('cta', '').split())
    
    total_words = hook_words + truth_words + cta_words
    
    # Calculate speaking time
    actual_wpm = base_wpm * speaking_rate
    speaking_time = (total_words / actual_wpm) * 60
    
    # Add pauses (from TTS configuration)
    pause_time = 0.3 + 0.5 + 0.3  # hook + truth + cta pauses
    
    # Add transition time (from video creation)
    transition_time = 3 * 0.4  # 3 clips × 0.2s fade each direction
    
    estimated_duration = speaking_time + pause_time + transition_time
    
    return {
        'estimated_seconds': round(estimated_duration, 2),
        'word_count': total_words,
        'speaking_time': round(speaking_time, 2),
        'pause_time': pause_time,
        'transition_time': transition_time,
        'breakdown': {
            'hook': hook_words,
            'truth': truth_words,
            'cta': cta_words
        }
    }


def build_motivational_prompt(scheduler_data, content_type, priority, intensity, trends, history):
    """
    Build prompt using SCHEDULER DATA + TRENDING - OPTIMIZED FOR 10-15 SECONDS
    """
    
    # Extract scheduler pillar info
    pillar = scheduler_data.get("decision", {}).get("current_pillar", {}) if scheduler_data else {}
    pillar_description = pillar.get("description", "Create powerful motivational content.")
    emotional_tone = pillar.get("emotional_tone", "commanding")
    pillar_keywords = pillar.get("keywords", ["discipline", "motivation"])
    
    print(f"🎯 Using Scheduler Pillar:")
    print(f"   Description: {pillar_description}")
    print(f"   Tone: {emotional_tone}")
    print(f"   Keywords: {', '.join(pillar_keywords[:5])}")
    
    # Get previous topics for context
    previous_topics = [t.get('title', '') for t in history['topics'][-15:]]
    
    # Extract trending topics
    trending_summaries = []
    if trends and trends.get('full_data'):
        for item in trends['full_data'][:5]:
            trending_summaries.append(f"• [{item.get('viral_score', 'N/A')}] {item['topic_title']}")
        print(f"🔥 Using {len(trending_summaries)} trending topics in prompt")
        trending_mandate = f"""
⚠️ MANDATORY REQUIREMENT ⚠️
You MUST create a script about ONE of these REAL trending topics:
{chr(10).join(trending_summaries)}
DO NOT make up your own topic.
"""
    else:
        trending_mandate = "⚠️ No trending data available - create original motivational content based on the pillar.\n"
    
    # Time context
    time_of_day = get_time_of_day(datetime.now().hour)
    
    # ✅ MODIFIED: Updated prompt for 10-15 second target
    prompt = f"""You are a scriptwriter for 'THE 5AM LEGION,' a hardcore motivational brand. Your tone is a fusion of David Goggins' intensity and Jocko Willink's authority.

SCHEDULER CONTEXT:
- Content Pillar: {content_type.replace('_', ' ').title()} ({pillar_description})
- Emotional Tone: {emotional_tone}
- Keywords: {', '.join(pillar_keywords)}
- Time of Day: {time_of_day}
- Intensity: {intensity}

{trending_mandate}

PREVIOUSLY COVERED (DO NOT REPEAT THESE):
{chr(10).join(f"  • {t}" for t in previous_topics) if previous_topics else '  None yet'}

TASK: Create a brutal, high-impact script for a 10-15 second YouTube Short optimized for MAXIMUM retention.

⚠️ CRITICAL DURATION CONSTRAINTS ⚠️
Your script MUST result in a 10-15 second final video. Every word counts.

MANDATORY 3-ACT SCRIPT STRUCTURE:

ACT 1: THE HOOK / THE PAIN (2-4 seconds)
- A brutally honest, relatable statement of pain
- MAXIMUM 8 WORDS
- Make them feel seen INSTANTLY
- No setup, no fluff - straight to the gut

ACT 2: THE TRUTH / THE REFRAME (5-7 seconds)
- Expose the lie behind the pain
- This is the core mindset shift
- MAXIMUM 15 WORDS
- Must be quotable and screenshot-worthy
- One powerful truth, not multiple points

ACT 3: THE ACTION / THE COMMAND (2-4 seconds)
- A simple, direct, non-negotiable command
- MAXIMUM 7 WORDS
- What to do RIGHT NOW
- No explanation, just the action

TOTAL SCRIPT: 23-30 WORDS MAXIMUM
TARGET DURATION: 10-15 SECONDS (STRICT)

WORD COUNT EXAMPLES (DO NOT EXCEED THESE):

✅ GOOD (28 words total):
Hook (7w): "You hit snooze. That's the problem right there."
Truth (15w): "Winners feel the same resistance. They just move anyway. No negotiation with the voice."
CTA (6w): "Set your alarm. Get up tomorrow."

❌ TOO LONG (38 words - REJECTED):
Hook: "You keep hitting the snooze button every single morning and wondering why..."
Truth: "Successful people feel exactly the same way you do but they understand that..."
CTA: "So starting tomorrow morning you need to make a choice to..."

OUTPUT FORMAT (JSON ONLY - NO OTHER TEXT):
{{
  "title": "ALL-CAPS TITLE UNDER 60 CHARS USING KEYWORDS",
  "hook": "ACT 1: Brutal honest hook. MAX 8 WORDS.",
  "bullets": [
    "ACT 2: Powerful quotable truth. MAX 15 WORDS."
  ],
  "cta": "ACT 3: Direct command. MAX 7 WORDS.",
  "hashtags": ["#5amlegion", "#discipline", "#motivation", "#mindset", "#shorts"],
  "description": "1-2 sentences continuing the intensity. Include keywords.",
  "visual_prompts": [
    "Visual for Act 1: Dark moody shot showing struggle.",
    "Visual for Act 2: Intense powerful shot showing action/strength.",
    "Visual for Act 3: Commanding resolute shot showing determination."
  ]
}}

REMEMBER:
- TOTAL WORDS: 23-30 MAXIMUM (non-negotiable)
- Hook: ≤8 words
- Truth: ≤15 words  
- CTA: ≤7 words
- Every word must EARN its place
- Retention depends on tight pacing
- 10-15 seconds = viral sweet spot
"""
    return prompt


def get_time_of_day(hour):
    """Get time of day description"""
    if 4 <= hour <= 6:
        return "early morning (5 AM warrior time)"
    elif 7 <= hour <= 11:
        return "morning (starting the day)"
    elif 12 <= hour <= 16:
        return "afternoon (midday grind)"
    elif 17 <= hour <= 21:
        return "evening (reflection time)"
    else:
        return "late night (2 AM accountability)"


def extract_json_from_response(raw_text):
    """Extract JSON from Gemini response"""
    json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', raw_text, re.DOTALL)
    if json_match:
        print("✅ Found JSON in code block")
        return json_match.group(1)
    
    json_match = re.search(r'\{.*\}', raw_text, re.DOTALL)
    if json_match:
        print("✅ Found raw JSON")
        return json_match.group(0)
    
    raise ValueError("No JSON found in response")


def clean_script_text(text):
    """Clean script text of problematic characters"""
    text = text.replace('"', '').replace('"', '')
    text = text.replace(''', "'").replace(''', "'")
    text = text.replace('\u2018', "'").replace('\u2019', "'")
    text = text.replace('\u201c', '').replace('\u201d', '')
    return text


def generate_motivational_script():
    """Main script generation function"""
    
    # Get context from environment
    content_type = os.getenv('CONTENT_TYPE', 'general')
    priority = os.getenv('PRIORITY', 'medium')
    intensity = os.getenv('INTENSITY', 'balanced')
    
    print(f"\n{'='*70}")
    print(f"🔥 GENERATING MOTIVATIONAL SCRIPT (10-15 SECOND TARGET)")
    print(f"{'='*70}")
    print(f"📍 Content Type: {content_type}")
    print(f"⭐ Priority: {priority}")
    
    # Load scheduler data, history, and trending
    scheduler_data = load_scheduler_data()
    history = load_history()
    trends = load_trending()
    
    if scheduler_data:
        print(f"✅ Loaded scheduler data")
    if trends:
        print(f"✅ Loaded trending data from {trends.get('source', 'unknown')}")
        print(f"   Topics: {len(trends.get('topics', []))}")
    else:
        print("⚠️ No trending data available")
    
    # Build prompt using ALL data
    prompt = build_motivational_prompt(scheduler_data, content_type, priority, intensity, trends, history)
    
    # Try generating with multiple attempts
    max_attempts = 5
    attempt = 0
    data = None
    
    while attempt < max_attempts:
        try:
            attempt += 1
            print(f"\n🔥 Generation attempt {attempt}/{max_attempts}...")
            
            raw_text = generate_script_with_retry(prompt)
            print(f"📝 Received response ({len(raw_text)} chars)")
            
            json_text = extract_json_from_response(raw_text)
            data = json.loads(json_text)
            
            validate_script_data(data)
            
            # ✅ NEW: Estimate and validate duration BEFORE accepting
            duration_estimate = estimate_script_duration(data)
            
            print(f"\n⏱️ Duration Estimate:")
            print(f"   Total words: {duration_estimate['word_count']}")
            print(f"   Hook: {duration_estimate['breakdown']['hook']}w")
            print(f"   Truth: {duration_estimate['breakdown']['truth']}w")
            print(f"   CTA: {duration_estimate['breakdown']['cta']}w")
            print(f"   Estimated duration: {duration_estimate['estimated_seconds']}s")
            
            # Reject if estimated duration is outside target range
            if duration_estimate['estimated_seconds'] > 16.0:
                raise ValueError(f"Script too long: {duration_estimate['estimated_seconds']}s (target: 10-15s)")
            
            if duration_estimate['estimated_seconds'] < 9.0:
                raise ValueError(f"Script too short: {duration_estimate['estimated_seconds']}s (target: 10-15s)")
            
            print(f"   ✅ Duration within target (10-15s)")
            
            data["topic"] = "motivation"
            data["content_type"] = content_type
            data["priority"] = priority
            data["intensity"] = intensity
            data["generated_at"] = datetime.now().isoformat()
            data["niche"] = "motivation"
            data["estimated_duration"] = duration_estimate['estimated_seconds']
            data["word_count"] = duration_estimate['word_count']
            
            data["title"] = clean_script_text(data["title"])
            data["hook"] = clean_script_text(data["hook"])
            data["cta"] = clean_script_text(data["cta"])
            data["bullets"] = [clean_script_text(b) for b in data["bullets"]]
            
            if "hashtags" not in data or not data["hashtags"]:
                data["hashtags"] = [
                    "#motivation", "#discipline", "#5am", "#mindset",
                    "#hustle", "#nodaysoff", "#shorts", "#warrior"
                ]
            
            if "description" not in data:
                data["description"] = f"{data['title']} - {data['hook']} #motivation #discipline #shorts"
            
            if "visual_prompts" not in data or len(data["visual_prompts"]) < 3:
                # Get the single Act 2 bullet safely
                act2_text = data['bullets'][0][:50] if data.get('bullets') else "transformation"
                
                data["visual_prompts"] = [
                    f"Dark contemplative scene for {data['hook'][:50]} person alone with thoughts moody lighting cinematic teal and orange high contrast",
                    f"Intense powerful moment for {act2_text} athlete pushing limits dramatic lighting slow motion sweat epic revelation",
                    f"Commanding action for {data['cta'][:50]} direct eye contact warrior stance triumphant resolving ready to execute"
                ]
            
            if "key_phrase" not in data:
                caps_match = re.search(r'\b[A-Z]{2,}(?:\s+[A-Z]{2,})*\b', data['title'])
                if caps_match:
                    data["key_phrase"] = caps_match.group(0)
                else:
                    words = data['title'].split()[:4]
                    data["key_phrase"] = ' '.join(words).upper()
            
            # Validate trending topics if available
            if trends and trends.get('topics'):
                if not validate_script_uses_trending_topic(data, trends['topics']):
                    raise ValueError("Script doesn't use trending topics - regenerating...")
            
            # Check for duplicates
            content_hash = get_content_hash(data)
            if content_hash in [t.get('hash') for t in history['topics']]:
                print("⚠️ Generated duplicate content, regenerating...")
                raise ValueError("Duplicate content detected")
            
            # Check for similar topics
            previous_titles = [t.get('title', '') for t in history['topics']]
            if is_similar_topic(data['title'], previous_titles):
                print("⚠️ Topic too similar to previous, regenerating...")
                raise ValueError("Similar topic detected")
            
            # Success!
            save_to_history(data['topic'], content_hash, data['title'], data)
            
            print(f"\n✅ SCRIPT GENERATED SUCCESSFULLY")
            print(f"   Title: {data['title']}")
            print(f"   Hook: {data['hook']}")
            print(f"   Key Phrase: {data.get('key_phrase', 'N/A')}")
            print(f"   Words: {duration_estimate['word_count']}")
            print(f"   Estimated: {duration_estimate['estimated_seconds']}s")
            print(f"   Hashtags: {', '.join(data['hashtags'][:5])}")
            
            break
            
        except json.JSONDecodeError as e:
            print(f"❌ Attempt {attempt} failed: JSON parse error - {e}")
            if attempt < max_attempts:
                print(f"   Retrying...")
        
        except ValueError as e:
            print(f"❌ Attempt {attempt} failed: {e}")
            if attempt < max_attempts:
                print(f"   Retrying...")
        
        except Exception as e:
            print(f"❌ Attempt {attempt} failed: {type(e).__name__} - {e}")
            if attempt < max_attempts:
                print(f"   Retrying...")
        
        if attempt >= max_attempts:
            print("\n⚠️ Max attempts reached, using fallback script...")
            data = get_fallback_script(content_type, intensity)
            fallback_hash = get_content_hash(data)
            save_to_history(data['topic'], fallback_hash, data['title'], data)
    
    # Save script to file
    script_path = os.path.join(TMP, "script.json")
    with open(script_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Saved script to {script_path}")
    
    # Save script text for TTS
    script_text_path = os.path.join(TMP, "script.txt")
    
    act1_hook = data.get('hook', 'The problem is not the clock.')
    # Get the first (and only) item from bullets for Act 2, with a fallback.
    act2_truth = data.get('bullets', ['The problem is what you do when it rings.'])[0] 
    act3_cta = data.get('cta', 'Get up.')
    
    # Assemble the full script for the TTS engine with pauses
    full_script = f"{act1_hook}\n\n{act2_truth}\n\n{act3_cta}"
    
    with open(script_text_path, "w", encoding="utf-8") as f:
        f.write(full_script)
    
    print(f"💾 Saved script text for TTS to {script_text_path}")
    
    # Summary
    print(f"\n{'='*70}")
    print(f"📊 GENERATION SUMMARY")
    print(f"{'='*70}")
    print(f"Total history: {len(history['topics'])} topics")
    print(f"Script length: {len(full_script.split())} words")
    print(f"Estimated duration: {data.get('estimated_duration', 'N/A')}s")
    print(f"Target: 10-15 seconds")
    print(f"Visual prompts: {len(data['visual_prompts'])}")
    
    if trends:
        print(f"\n🌐 Trending source: {trends.get('source', 'unknown')}")
    
    return data


def get_fallback_script(content_type, intensity):
    """Fallback script if all generation attempts fail - OPTIMIZED FOR 10-15s"""
    
    fallback_scripts = {
        'early_morning': {
            'title': "YOU'RE NOT TIRED YOU'RE UNDISCIPLINED",
            'hook': "You slept 8 hours. What's the problem.",  # 7 words
            'bullets': [
                "You negotiate with weakness. Winners don't wait for motivation."  # 10 words
            ],
            'cta': "Set alarm. Get up. Win.",  # 5 words
            'key_phrase': "DISCIPLINE OVER COMFORT"
        },
        'late_night': {
            'title': "THE TRUTH YOU NEED AT 2 AM",
            'hook': "You can't sleep. Your potential is haunting you.",  # 8 words
            'bullets': [
                "Another day wasted on distraction. Tomorrow you die or rise."  # 11 words
            ],
            'cta': "Decide now. Tomorrow is different.",  # 5 words
            'key_phrase': "THE OLD YOU DIES TONIGHT"
        },
        'midday': {
            'title': "NOBODY IS COMING TO SAVE YOU",
            'hook': "You're waiting for permission to start living.",  # 7 words
            'bullets': [
                "It won't arrive. The cavalry isn't coming. You're alone."  # 10 words
            ],
            'cta': "Save yourself. Start now.",  # 4 words
            'key_phrase': "SAVE YOURSELF"
        },
        'evening': {
            'title': "THE DAY IS OVER. DID YOU WIN?",
            'hook': "Look at today with brutal honesty.",  # 6 words
            'bullets': [
                "Were you busy or productive. You know the difference already."  # 11 words
            ],
            'cta': "Plan tomorrow's victory tonight.",  # 4 words
            'key_phrase': "DID YOU WIN TODAY"
        }
    }

    selected = fallback_scripts.get(content_type, fallback_scripts['midday'])
    
    return {
        'title': selected['title'],
        'topic': 'motivation',
        'hook': selected.get('hook'),
        'bullets': selected.get('bullets'),
        'cta': selected.get('cta'),
        'key_phrase': selected.get('key_phrase'),
        'hashtags': ['#motivation', '#discipline', '#5am', '#mindset', '#shorts'],
        'description': f"{selected['title']} - Stop making excuses. #motivation #discipline",
        'visual_prompts': [
            'Person alone in dark room contemplating life choices, moody blue lighting, cinematic.',
            'Intense gym training montage, athlete pushing through pain, dramatic lighting.',
            'Close-up on determined eyes, warrior mindset, ready for battle, sharp focus.'
        ],
        'content_type': content_type,
        'priority': 'fallback',
        'intensity': intensity,
        'is_fallback': True,
        'generated_at': datetime.now().isoformat(),
        'niche': 'motivation',
        'estimated_duration': 12.0,
        'word_count': 22
    }


if __name__ == '__main__':
    try:
        generate_motivational_script()
        print("\n✅ Script generation complete!")
    except Exception as e:
        print(f"\n❌ FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        exit(1)