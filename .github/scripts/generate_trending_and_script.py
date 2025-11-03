#!/usr/bin/env python3
"""
🔥 Generate Motivational Script - SCHEDULER-INTEGRATED VERSION
Creates emotionally charged motivational scripts using:
- Scheduler data (pillar, tone, keywords)
- Trending topics (real-time viral content)
- Content history (avoid duplicates)
- Retry logic with exponential backoff
- Robust JSON parsing
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
    """Validate generated script has all required fields for the new 3-act structure"""
    required_fields = ["title", "hook", "bullets", "cta"]
    
    for field in required_fields:
        if field not in data or not data[field]:
            raise ValueError(f"Missing or empty required field: {field}")
    
    if not isinstance(data["bullets"], list) or len(data["bullets"]) != 1:
        raise ValueError("'bullets' must be a list containing exactly one item for Act 2.")
    
    if not data["bullets"][0] or len(data["bullets"][0]) < 5:
        raise ValueError("The bullet for Act 2 is too short or empty.")
    
    if len(data["title"]) > 70:
        print(f"⚠️ Title too long ({len(data['title'])} chars), truncating...")
        data["title"] = data["title"][:67] + "..."
    
    if len(data["hook"].split()) > 15:
        print(f"⚠️ Hook too long ({len(data['hook'].split())} words), shortening...")
        words = data["hook"].split()[:12]
        data["hook"] = " ".join(words)
        
    return True


# In generate_trending_and_script.py
# ACTION: Replace your entire build_motivational_prompt function with this one.

def build_motivational_prompt(scheduler_data, content_type, priority, intensity, trends, history):
    """Build prompt using SCHEDULER DATA + TRENDING - FOCUSED 3-ACT VERSION"""
    
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
    
    # Build the enhanced prompt
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

TASK: Create a brutal, high-impact script for a 20-30 second YouTube Short. It must hold 100% audience retention.

MANDATORY 3-ACT SCRIPT STRUCTURE:

ACT 1: THE HOOK / THE PAIN (0-4 seconds)
- A brutally honest, relatable statement of pain. Under 12 words. Make them feel seen INSTANTLY.

ACT 2: THE TRUTH / THE REFRAME (4-15 seconds)
- Expose the lie behind the pain. This is the core mindset shift. A short, powerful, quotable statement. Under 15 words.

ACT 3: THE ACTION / THE COMMAND (15-25 seconds)
- A simple, direct, non-negotiable command for IMMEDIATE action. What to do RIGHT NOW. Under 10 words.

OUTPUT FORMAT (JSON ONLY - NO OTHER TEXT):
{{
  "title": "ALL-CAPS TITLE UNDER 60 CHARS USING KEYWORDS",
  "hook": "ACT 1: The brutal, honest hook. Under 12 words.",
  "bullets": [
    "ACT 2: The powerful, quotable truth/reframe. Under 15 words."
  ],
  "cta": "ACT 3: The direct, immediate command. Under 10 words.",
  "hashtags": ["#5amlegion", "#discipline", "#motivation", "#mindset", "#shorts"],
  "description": "A 1-2 sentence description continuing the intensity. Incorporate keywords.",
  "visual_prompts": [
    "Visual for Act 1: Dark, moody shot showing struggle or contemplation.",
    "Visual for Act 2: Intense, powerful shot showing action or strength (e.g., training, lion).",
    "Visual for Act 3: Commanding, resolute shot (e.g., close-up on determined eyes, starting an action)."
  ]
}}
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
    
    print(f"\n{'='*70}")
    print(f"🔥 GENERATING MOTIVATIONAL SCRIPT")
    print(f"{'='*70}")
    print(f"📍 Content Type: {content_type}")
    print(f"⭐ Priority: {priority}")
    print(f"⚡ Intensity: {intensity}")
    
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
            
            data["topic"] = "motivation"
            data["content_type"] = content_type
            data["priority"] = priority
            data["intensity"] = intensity
            data["generated_at"] = datetime.now().isoformat()
            data["niche"] = "motivation"
            
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
            
            if "visual_prompts" not in data or len(data["visual_prompts"]) < 4:
                data["visual_prompts"] = [
                    f"Dark contemplative scene for {data['hook'][:50]} person alone with thoughts moody lighting cinematic teal and orange high contrast",
                    f"Intense training for {data['bullets'][0][:50]} athlete pushing limits dramatic lighting slow motion sweat",
                    f"Epic journey for {data['bullets'][1][:50]} mountain summit sunrise powerful aspirational wide cinematic",
                    f"Commanding action for {data['bullets'][2][:50]} direct eye contact warrior stance triumphant resolving"
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
            print(f"   Bullets: {len(data['bullets'])} points")
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
    
    # =================== START: REPLACE THIS BLOCK ===================
    # Save script text for TTS
    script_text_path = os.path.join(TMP, "script.txt")
    full_script = f"{data['hook']}\n\n"
    full_script += "\n\n".join(data['bullets'])
    full_script += f"\n\n{data['cta']}"
    
    with open(script_text_path, "w", encoding="utf-8") as f:
        f.write(full_script)
    # =================== END: REPLACE THIS BLOCK ===================

    # WITH THIS NEW, 3-ACT ASSEMBLY LOGIC:
    # =================== START: NEW CODE ===================
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
    # =================== END: NEW CODE ===================
    
    print(f"💾 Saved script text for TTS to {script_text_path}")
    
    # Summary
    print(f"\n{'='*70}")
    print(f"📊 GENERATION SUMMARY")
    print(f"{'='*70}")
    print(f"Total history: {len(history['topics'])} topics")
    print(f"Script length: {len(full_script.split())} words")
    print(f"Visual prompts: {len(data['visual_prompts'])}")
    
    if trends:
        print(f"\n🌐 Trending source: {trends.get('source', 'unknown')}")
    
    return data


def get_fallback_script(content_type, intensity):
    """Fallback script if all generation attempts fail"""
    
    fallback_scripts = {
        'early_morning': {
            'title': "YOU'RE NOT TIRED YOU'RE UNDISCIPLINED",
            'hook': "You slept 8 hours. The problem isn't your body.",
            'bullets': [
                "The problem is you negotiate with the voice of weakness."
            ],
            'cta': "Win the first battle. Get up.",
            'key_phrase': "DISCIPLINE OVER COMFORT"
        },
        'late_night': {
            'title': "THE TRUTH YOU NEED TO HEAR AT 2 AM",
            'hook': "You can't sleep because your potential is haunting you.",
            'bullets': [
                "Another day is gone, wasted on distraction and doubt."
            ],
            'cta': "Decide now. Tomorrow is different.",
            'key_phrase': "THE OLD YOU DIES TONIGHT"
        },
        'midday': {
            'title': "NOBODY IS COMING TO SAVE YOU",
            'hook': "You are waiting for a permission slip to start your life.",
            'bullets': [
                "It will never arrive. The cavalry isn't coming."
            ],
            'cta': "Save yourself. Start now.",
            'key_phrase': "SAVE YOURSELF"
        },
        'evening': {
            'title': "THE DAY IS OVER. DID YOU WIN?",
            'hook': "Look at the last 12 hours with brutal honesty.",
            'bullets': [
                "Were you busy, or were you productive? You know the difference."
            ],
            'cta': "Plan tomorrow's victory tonight.",
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
        'description': f"{selected['title']} - Stop making excuses and start taking action. #motivation #discipline",
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
        'niche': 'motivation'
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