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
    """Validate generated script has all required fields"""
    required_fields = ["title", "topic", "hook", "bullets", "cta"]
    
    for field in required_fields:
        if field not in data:
            raise ValueError(f"Missing required field: {field}")
    
    if not isinstance(data["bullets"], list) or len(data["bullets"]) < 3:
        raise ValueError("bullets must be a list with at least 3 items")
    
    for i, bullet in enumerate(data["bullets"]):
        if not bullet or len(bullet) < 10:
            raise ValueError(f"Bullet {i+1} is too short or empty")
    
    if len(data["title"]) > 100:
        print(f"⚠️ Title too long ({len(data['title'])} chars), truncating...")
        data["title"] = data["title"][:97] + "..."
    
    if len(data["hook"].split()) > 15:
        print(f"⚠️ Hook too long ({len(data['hook'].split())} words), shortening...")
        words = data["hook"].split()[:12]
        data["hook"] = " ".join(words)
    
    return True


def build_motivational_prompt(scheduler_data, content_type, priority, intensity, trends, history):
    """Build prompt using SCHEDULER DATA + TRENDING"""
    
    # Extract scheduler pillar info
    pillar = scheduler_data.get("decision", {}).get("current_pillar", {}) if scheduler_data else {}
    
    pillar_description = pillar.get("description", "")
    emotional_tone = pillar.get("emotional_tone", "")
    pillar_keywords = pillar.get("keywords", [])
    
    print(f"🎯 Using Scheduler Pillar:")
    print(f"   Description: {pillar_description}")
    print(f"   Tone: {emotional_tone}")
    print(f"   Keywords: {', '.join(pillar_keywords[:5])}")
    
    # Get previous topics for context
    previous_topics = [
        f"{t.get('topic', 'unknown')}: {t.get('title', '')}" 
        for t in history['topics'][-20:]
    ]
    previous_titles = [t.get('title', '') for t in history['topics'][-30:]]
    
    # Extract trending topics
    trending_topics = []
    trending_summaries = []
    
    if trends and trends.get('topics'):
        trending_topics = trends['topics'][:5]
        full_data = trends.get('full_data', [])
        
        if full_data:
            for item in full_data[:5]:
                viral_score = item.get('viral_score', 'N/A')
                trending_summaries.append(
                    f"• [{viral_score}] {item['topic_title']}\n"
                    f"  Hook: {item.get('hook_angle', 'N/A')}\n"
                    f"  Pain: {item.get('target_pain', 'N/A')}\n"
                    f"  CTA: {item.get('cta_idea', 'N/A')}"
                )
        else:
            trending_summaries = [f"• {t}" for t in trending_topics]
        
        print(f"🔥 Using {len(trending_topics)} trending topics in prompt")
    
    # Build trending mandate
    if trending_topics:
        trending_mandate = f"""
⚠️⚠️⚠️ CRITICAL MANDATORY REQUIREMENT ⚠️⚠️⚠️

YOU MUST CREATE A SCRIPT ABOUT ONE OF THESE REAL TRENDING MOTIVATIONAL TOPICS:

{chr(10).join(trending_summaries)}

These are REAL trends from today ({datetime.now().strftime('%Y-%m-%d %H:%M')}) collected from:
- Google Trends (real motivational search data)
- Reddit communities (r/GetMotivated, r/GetDisciplined)
- YouTube trending (viral motivational content)
- Evergreen themes (proven viral topics)

YOU MUST PICK ONE OF THE 5 TOPICS ABOVE AND EXPAND IT INTO A VIRAL SCRIPT.
DO NOT create content about anything else.
DO NOT make up your own topic.
USE THE EXACT TREND, including the suggested hook, pain point, and CTA.
"""
    else:
        trending_mandate = "⚠️ No trending data available - create original motivational content\n"
    
    # Content type specific guidance
    content_type_guidance = get_content_type_guidance(content_type, emotional_tone)
    
    # Intensity guidance
    intensity_guidance = get_intensity_guidance(intensity)
    
    # Time context
    current_hour = datetime.now().hour
    time_of_day = get_time_of_day(current_hour)
    
    # Build the enhanced prompt
    prompt = f"""You are a viral motivational content creator - a fusion of David Goggins' raw intensity, Eric Thomas' emotional fire, and Jocko Willink's disciplined authority.

SCHEDULER CONTEXT (FROM OPTIMAL POSTING TIME ALGORITHM):
- Content Pillar: {content_type.replace('_', ' ').title()}
- Pillar Description: {pillar_description}
- Emotional Tone: {emotional_tone}
- Pillar Keywords: {', '.join(pillar_keywords)}
- Priority Level: {priority.upper()}

POSTING TIME CONTEXT:
- Current date: {datetime.now().strftime('%Y-%m-%d')}
- Current time: {datetime.now().strftime('%I:%M %p')}
- Time of day: {time_of_day}
- Intensity: {intensity}

PREVIOUSLY COVERED (DO NOT REPEAT):
{chr(10).join(f"  • {t}" for t in previous_topics[-15:]) if previous_topics else '  None yet'}

{trending_mandate}

TASK: Create a SOUL-CRUSHING, transformative MOTIVATIONAL script for a 60-90 second YouTube Short.

MANDATORY REQUIREMENTS:

✅ Use the emotional tone: {emotional_tone}
✅ Incorporate these keywords: {', '.join(pillar_keywords)}
✅ Start with PAIN - make them feel the weight of wasted potential
✅ Use "YOU" language - direct, personal, intimate
✅ Be BRUTALLY honest - no sugarcoating
✅ Build URGENCY - time is running out
✅ Give SPECIFIC action steps - what to do RIGHT NOW
✅ End with IDENTITY shift - declare who they're becoming
✅ Use SHORT, PUNCHY sentences for impact (5-10 words max)
✅ Include strategic PAUSES (use "..." for dramatic effect)
✅ Create QUOTABLE moments (people will screenshot)
✅ Hit EMOTIONAL PAIN POINTS immediately
✅ Topic must be COMPLETELY DIFFERENT from previous topics above
✅ Make it ACTIONABLE - what to do RIGHT NOW (not tomorrow)
✅ Avoid generic platitudes - be raw and unfiltered
✅ NO special characters or quotes in output (breaks parsing)

{content_type_guidance}

{intensity_guidance}

EMOTIONAL JOURNEY (MANDATORY 5-ACT STRUCTURE):

ACT 1: THE PAIN (0-10 seconds)
- Hit them with uncomfortable truth about wasted potential
- Make them feel SEEN in their struggle
- Use "YOU" language - direct, personal, intimate
- Tone: {emotional_tone}

ACT 2: THE WAKE-UP CALL (10-25 seconds)
- Expose their excuses as lies
- Create urgency - time is running out
- Show what they're missing while they wait

ACT 3: THE TRANSFORMATION (25-55 seconds)
- Reveal what changes everything
- Show the path winners take
- Give them the mindset shift

ACT 4: THE CALL TO ACTION (55-75 seconds)
- Command immediate action - RIGHT NOW
- Give specific first step
- Make it impossible to ignore

ACT 5: THE DECLARATION (75-90 seconds)
- Seal the identity shift
- Declare who they're becoming
- End with power and conviction

POWER PHRASES TO INCORPORATE:
- "While you sleep they grind"
- "Your comfort zone is killing you"
- "Stop negotiating with yourself"
- "Discipline is doing it anyway"
- "The old you died today"
- "Nobody's coming to save you"
- "Your future self is watching"
- "Weak people quit Winners persist"

SPECIFICITY RULES (VERY IMPORTANT):

❌ VAGUE: Wake up early and work hard
✅ SPECIFIC: Set your alarm for 5 AM and get up when it rings no snooze no negotiation

❌ VAGUE: Stop making excuses and take action
✅ SPECIFIC: Close this app right now do one push-up prove to yourself you can keep a promise

❌ VAGUE: Be disciplined and consistent
✅ SPECIFIC: Do the hard thing for the next 7 days straight track it in your notes every single day

OUTPUT FORMAT (JSON ONLY - NO OTHER TEXT BEFORE OR AFTER):
{{
  "title": "Aggressive commanding title with urgency under 60 chars with CAPS key phrase using pillar keywords",
  "topic": "motivation",
  "hook": "Brutal opening truth that hits them immediately under 12 words matching emotional tone",
  "bullets": [
    "First emotional punch - raw truth about their situation incorporating pillar keywords 15-20 words",
    "Second wake-up call - what they're missing while they wait using pillar theme 15-20 words",
    "Third transformation - the path forward with specific action matching content pillar 15-20 words"
  ],
  "cta": "Direct command for immediate action RIGHT NOW under 12 words",
  "hashtags": ["#motivation", "#discipline", "#5am", "#mindset", "#hustle", "#nodaysoff", "#shorts", "#warrior"],
  "description": "2-3 sentences that continue the intensity and include searchable keywords",
  "visual_prompts": [
    "Dark moody shot for pain section matching emotional tone cinematic lighting teal and orange grade high contrast",
    "Intense training montage for wake-up section athlete pushing limits slow motion dramatic lighting sweat and effort",
    "Epic journey shot for transformation section mountain summit at sunrise powerful and aspirational wide cinematic",
    "Commanding action shot for CTA section direct eye contact warrior stance triumphant and resolving"
  ]
}}

EXAMPLE OUTPUT:
{{
  "title": "YOU'RE NOT TIRED YOU'RE UNDISCIPLINED Wake Up Call",
  "topic": "motivation",
  "hook": "You slept 8 hours so what's the real problem",
  "bullets": [
    "You say you don't have time but you watched Netflix for 3 hours yesterday you're not busy you're distracted and you know it",
    "Successful people feel the exact same resistance the exact same fear the exact same voice saying tomorrow but they move anyway they don't wait",
    "Set your alarm for 5 AM right now tomorrow morning when it goes off you get up no snooze no negotiation prove you're serious"
  ],
  "cta": "Close this app set your alarm right now prove it",
  "hashtags": ["#motivation", "#discipline", "#5am", "#nodaysoff", "#mindset", "#shorts", "#warrior", "#goggins"],
  "description": "Stop making excuses and start building discipline. Winners don't wake up motivated - they wake up and do it anyway. Your 5 AM awaits.",
  "visual_prompts": [
    "Dark bedroom at night person lying awake contemplating moody blue lighting teal grade high contrast cinematic",
    "Intense gym session athlete covered in sweat pushing through exhaustion slow motion dramatic lighting",
    "Mountain summit at dawn lone figure standing triumphant powerful and aspirational wide cinematic",
    "Close-up determined eyes focused warrior mindset sharp contrast commanding presence"
  ]
}}

REMEMBER:
- YOU MUST USE ONE OF THE 5 TRENDING TOPICS IF PROVIDED
- Be BRUTALLY HONEST - no sugarcoating
- Make it COMPLETELY DIFFERENT from previous topics
- Hit EMOTIONAL PAIN POINTS immediately
- Create URGENCY - they must act RIGHT NOW
- End with IDENTITY SHIFT - who they're becoming
- NO SPECIAL CHARACTERS in output (breaks JSON)
- USE PILLAR KEYWORDS: {', '.join(pillar_keywords)}
- MATCH EMOTIONAL TONE: {emotional_tone}
"""

    return prompt


def get_content_type_guidance(content_type, emotional_tone):
    """Get specific guidance for content type with tone"""
    guidance = {
        'early_morning': f"""
MORNING FIRE FOCUS (5-7 AM):
- Open with 5 AM energy ("While they sleep in you rise")
- Emphasize discipline over comfort
- Emotional tone: {emotional_tone}
- Call to action: Set alarm get up no snooze
- Energy: High commanding military-style
- Target: Early risers discipline seekers 5 AM warriors
- Example: "5 AM That's when champions are made While the world sleeps you grind"
""",
        'late_night': f"""
LATE NIGHT ACCOUNTABILITY FOCUS (10 PM-2 AM):
- Open with "You're reading this at [time] because..."
- Address guilt/regret about wasted day
- Emotional tone: {emotional_tone}
- Call to action: Set alarm for tomorrow start fresh
- Energy: Intimate honest brother-to-brother
- Target: Late night scrollers people with regret insomniacs questioning life
- Example: "You can't sleep because you know you wasted today Tomorrow starts now Set your alarm"
""",
        'midday': f"""
MIDDAY BOOST FOCUS (11 AM-3 PM):
- Open with "Halfway through the day what have you accomplished"
- Push through afternoon slump
- Emotional tone: {emotional_tone}
- Call to action: Do the hard thing NOW
- Energy: Urgent no-nonsense direct
- Target: Procrastinators midday break scrollers people losing momentum
- Example: "Stop scrolling Stop procrastinating Get back to work Now"
""",
        'evening': f"""
EVENING REFLECTION FOCUS (6-9 PM):
- Open with "Today's almost over Did you win or make excuses"
- Reflect on day prepare for tomorrow
- Emotional tone: {emotional_tone}
- Call to action: Plan tomorrow review goals
- Energy: Reflective but powerful accountability
- Target: Evening planners people reviewing their day goal-setters
- Example: "What did you actually accomplish today Tomorrow no excuses"
""",
        'general': f"""
GENERAL MOTIVATION FOCUS:
- Universal discipline and mindset themes
- Balanced approach works any time
- Emotional tone: {emotional_tone}
- Call to action: Start now not tomorrow
- Energy: Powerful but adaptable
- Target: General motivation seekers self-improvement enthusiasts
- Example: "Stop waiting for motivation Discipline is the only thing that matters"
"""
    }
    return guidance.get(content_type, guidance['general'])


def get_intensity_guidance(intensity):
    """Get guidance for intensity level"""
    levels = {
        'aggressive': """
AGGRESSIVE INTENSITY:
- Very direct almost harsh truth
- No softening pure raw reality
- Strong language OK (not profane)
- Channel David Goggins energy
- Examples: "Stop being soft" "Quit being weak" "You're better than this pathetic version"
""",
        'balanced': """
BALANCED INTENSITY:
- Firm but encouraging
- Honest without being harsh
- Push them but show them the way
- Channel Jocko Willink energy
- Examples: "You're stronger than this" "Time to step up" "You know what you need to do"
""",
        'inspirational': """
INSPIRATIONAL INTENSITY:
- Uplifting and empowering
- Focus on potential and possibility
- Encouraging but still urgent
- Channel Eric Thomas energy
- Examples: "You're capable of greatness" "This is your moment" "Your time is now"
"""
    }
    return levels.get(intensity, levels['balanced'])


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
    
    # Save script text for TTS
    script_text_path = os.path.join(TMP, "script.txt")
    full_script = f"{data['hook']}\n\n"
    full_script += "\n\n".join(data['bullets'])
    full_script += f"\n\n{data['cta']}"
    
    with open(script_text_path, "w", encoding="utf-8") as f:
        f.write(full_script)
    
    print(f"💾 Saved script text to {script_text_path}")
    
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
            'title': "YOU'RE NOT TIRED YOU'RE UNDISCIPLINED Wake Up",
            'hook': "You slept 8 hours so what's the real problem",
            'bullets': [
                "You say you don't have time but you watched Netflix for 3 hours yesterday you're not busy you're distracted and you know it",
                "Successful people feel the exact same resistance the exact same fear the exact same voice saying tomorrow but they move anyway they don't wait",
                "Set your alarm for 5 AM right now tomorrow morning when it goes off you get up no snooze no negotiation prove you're serious"
            ],
            'key_phrase': "DISCIPLINE BEATS MOTIVATION"
        },
        'late_night': {
            'title': "READING THIS AT 2 AM Here's The Truth",
            'hook': "You can't sleep because you wasted today",
            'bullets': [
                "You scrolled for hours made plans you didn't execute and now you're here feeling guilty about another wasted day the cycle continues",
                "Tomorrow is decided tonight You can lie here feeling bad or make one decision right now that changes everything set your alarm",
                "The old you who makes excuses and wastes time dies tonight Tomorrow morning a new you wakes up someone who keeps their word"
            ],
            'key_phrase': "THE OLD YOU DIES TONIGHT"
        },
        'midday': {
            'title': "NOBODY'S COMING TO SAVE YOU Save Yourself",
            'hook': "You're waiting for someone to rescue you",
            'bullets': [
                "You keep hoping things will magically get better hoping someone will give you permission hoping the perfect moment arrives but it never does",
                "Every successful person you admire started exactly where you are right now afraid and uncertain but they moved anyway without permission",
                "Start today with what you have do the smallest thing right now one push-up one page one call just prove to yourself you can move"
            ],
            'key_phrase': "NOBODY'S COMING"
        },
        'evening': {
            'title': "WHAT DID YOU BUILD TODAY Evening Check",
            'hook': "Today's almost over did you win",
            'bullets': [
                "You were busy all day but what did you actually accomplish motion doesn't equal progress activity doesn't equal achievement you know the difference",
                "Winners reflect on their day with honesty they don't lie to themselves they see what worked what didn't and they adjust for tomorrow",
                "Before you sleep review today plan tomorrow write down your three most important tasks and commit to doing them no matter what"
            ],
            'key_phrase': "DID YOU WIN TODAY"
        }
    }
    
    selected = fallback_scripts.get(content_type, fallback_scripts['midday'])
    
    return {
        'title': selected['title'],
        'topic': 'motivation',
        'hook': selected['hook'],
        'bullets': selected['bullets'],
        'key_phrase': selected['key_phrase'],
        'cta': 'Take action right now not tomorrow',
        'hashtags': ['#motivation', '#discipline', '#5am', '#mindset', '#hustle', '#nodaysoff', '#shorts', '#warrior'],
        'description': f"{selected['title']} - Stop making excuses and start taking action. The old you dies today. #motivation #discipline #shorts",
        'visual_prompts': [
            'Person alone in dark room contemplating life choices moody blue lighting teal and orange color grade high contrast cinematic',
            'Intense gym training montage athlete pushing through pain sweat dripping slow motion dramatic lighting inspirational',
            'Mountain summit at sunrise lone figure standing tall victorious powerful aspirational wide cinematic shot',
            'Close-up determined eyes warrior mindset ready for battle sharp focus commanding presence'
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