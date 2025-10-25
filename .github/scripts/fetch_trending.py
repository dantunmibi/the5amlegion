#!/usr/bin/env python3
"""
🔍 Fetch Trending Mystery Topics - ROBUST VERSION
Multi-source trending data collector for mystery niche
Sources: Google Trends, Reddit, YouTube, Evergreen mystery themes
"""

import json
import time
import random
import os
import re
from typing import List, Dict, Any
from datetime import datetime, timedelta
import google.generativeai as genai
import requests
from bs4 import BeautifulSoup

# Configure Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Model selection (same as your original)
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

TMP = os.getenv("GITHUB_WORKSPACE", ".") + "/tmp"
os.makedirs(TMP, exist_ok=True)


def get_google_trends_mystery() -> List[str]:
    """Get real trending mystery searches from Google Trends"""
    try:
        from pytrends.request import TrendReq
        
        print(f"🔍 Fetching Google Trends (Mysteries & Unsolved Cases)...")
        
        try:
            pytrends = TrendReq(hl='en-US', tz=360, timeout=(10, 25))
        except Exception as init_error:
            print(f"   ⚠️ PyTrends initialization failed: {init_error}")
            return []
        
        relevant_trends = []
        
        # 🔍 MYSTERY-SPECIFIC KEYWORDS
        mystery_topics = [
            # Unsolved mysteries (general)
            'unsolved mysteries',
            'true crime unsolved',
            'cold case',
            'missing person case',
            
            # Famous cases
            'bermuda triangle',
            'db cooper',
            'zodiac killer',
            'dyatlov pass',
            'flight 19',
            'malaysia airlines mh370',
            
            # True crime
            'true crime documentary',
            'unsolved murder',
            'cold case solved',
            'criminal investigation',
            
            # Historical mysteries
            'ancient mysteries',
            'unexplained discoveries',
            'archaeological mystery',
            'voynich manuscript',
            'antikythera mechanism',
            
            # Paranormal/unexplained
            'unexplained disappearance',
            'strange phenomena',
            'conspiracy theories',
            'declassified documents',
            
            # Actionable (people searching for content)
            'mystery documentary',
            'unsolved cases 2024',
            'true crime podcast',
            'mystery youtube'
        ]
        
        for topic in mystery_topics:
            try:
                print(f"   🔍 Searching trends for: {topic}")
                pytrends.build_payload([topic], timeframe='now 7-d', geo='US')
                
                # Get related queries
                related = pytrends.related_queries()
                
                if topic in related and 'top' in related[topic]:
                    top_queries = related[topic]['top']
                    if top_queries is not None and not top_queries.empty:
                        for query in top_queries['query'].head(5):
                            # Filter for mystery relevance
                            if len(query) > 10 and is_mystery_query(query):
                                relevant_trends.append(query)
                                print(f"      ✓ {query}")
                
                # Also check rising queries (viral potential)
                if topic in related and 'rising' in related[topic]:
                    rising_queries = related[topic]['rising']
                    if rising_queries is not None and not rising_queries.empty:
                        for query in rising_queries['query'].head(3):
                            if len(query) > 10 and is_mystery_query(query):
                                relevant_trends.append(f"{query} (🔥 RISING)")
                                print(f"      🔥 {query} (RISING)")
                
                time.sleep(random.uniform(1.5, 3.0))  # Respectful rate limiting
                
            except Exception as e:
                print(f"   ⚠️ Failed for '{topic}': {str(e)[:50]}...")
                continue
        
        print(f"✅ Found {len(relevant_trends)} mystery trends from Google")
        return relevant_trends[:20]
        
    except ImportError:
        print("⚠️ pytrends not installed - skipping Google Trends")
        print("   Install with: pip install pytrends")
        return []
    except Exception as e:
        print(f"⚠️ Google Trends failed: {e}")
        return []


def is_mystery_query(query: str) -> bool:
    """Filter for mystery relevance"""
    query_lower = query.lower()
    
    # Good mystery keywords
    good_keywords = [
        'mystery', 'unsolved', 'disappear', 'missing', 'cold case',
        'murder', 'killer', 'crime', 'investigation', 'detective',
        'conspiracy', 'unexplained', 'strange', 'phenomenon',
        'ancient', 'artifact', 'discovery', 'declassified',
        'cipher', 'code', 'secret', 'hidden', 'vanish',
        'bermuda', 'zodiac', 'cooper', 'flight 19', 'dyatlov',
        'true crime', 'documentary', 'case', 'evidence'
    ]
    
    # Avoid non-mystery topics
    bad_keywords = [
        'song', 'music', 'movie', 'trailer', 'game', 'anime',
        'celebrity gossip', 'dating', 'relationship',
        'recipe', 'workout', 'fashion', 'makeup',
        'price', 'buy', 'shop', 'sale', 'review'
    ]
    
    has_good = any(kw in query_lower for kw in good_keywords)
    has_bad = any(kw in query_lower for kw in bad_keywords)
    
    return has_good and not has_bad


def get_reddit_mystery_trends() -> List[str]:
    """Get trending posts from mystery/true crime subreddits"""
    try:
        print("🔍 Fetching Reddit mystery trends...")
        
        # 🔍 MYSTERY-SPECIFIC SUBREDDITS
        subreddits = [
            'UnresolvedMysteries',    # 1.9M+ members (GOLD MINE)
            'TrueCrime',              # 500K+ members
            'UnexplainedPhotos',      # 300K+ members
            'HighStrangeness',        # 400K+ members
            'conspiracy',             # 2M+ (filter for declassified only)
            'ColdCases',              # True crime cold cases
            'Mystery',                # General mysteries
            'CrimeScene',             # Crime investigation
            'serialkillers',          # True crime (famous cases)
            'Missing411',             # Unexplained disappearances
            'AlternativeHistory',     # Historical mysteries
            'AncientAliens'           # Ancient mysteries (filter for facts)
        ]
        
        trends = []
        
        for subreddit in subreddits:
            try:
                url = f'https://www.reddit.com/r/{subreddit}/hot.json?limit=25'
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                }
                
                print(f"   📱 Fetching r/{subreddit}...")
                response = requests.get(url, headers=headers, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    posts_found = 0
                    
                    for post in data['data']['children'][:20]:
                        post_data = post['data']
                        title = post_data.get('title', '')
                        upvotes = post_data.get('ups', 0)
                        
                        # 🔍 MYSTERY-SPECIFIC FILTERING
                        good_phrases = [
                            # Unsolved cases
                            'unsolved', 'mystery', 'never solved', 'still unknown',
                            'no explanation', 'unexplained', 'strange case',
                            
                            # Disappearances
                            'disappeared', 'vanished', 'missing', 'never found',
                            'no trace', 'last seen',
                            
                            # Investigations
                            'case of', 'investigation', 'evidence', 'clues',
                            'what happened to', 'the truth about',
                            
                            # Historical
                            'ancient', 'artifact', 'discovery', 'archaeological',
                            'declassified', 'documents reveal',
                            
                            # True crime
                            'murder', 'killer', 'victim', 'suspect',
                            'cold case', 'true crime'
                        ]
                        
                        # Reject irrelevant posts
                        bad_phrases = [
                            'what do you think', 'unpopular opinion', 'am i the only',
                            'dae', 'discussion thread', 'meta', 'subreddit',
                            'looking for', 'can someone help', 'does anyone know',
                            'rant', 'off topic', 'question about', 'eli5'
                        ]
                        
                        title_lower = title.lower()
                        
                        has_good = any(phrase in title_lower for phrase in good_phrases)
                        has_bad = any(phrase in title_lower for phrase in bad_phrases)
                        
                        # Prioritize high-engagement posts
                        is_viral = upvotes > 500
                        
                        if (has_good and not has_bad) or is_viral:
                            # Clean up title
                            clean_title = clean_reddit_title(title)
                            if clean_title and len(clean_title) > 15:
                                trends.append(clean_title)
                                posts_found += 1
                                viral_marker = " 🔥" if is_viral else ""
                                print(f"      ✓ ({upvotes} ↑) {clean_title[:70]}{viral_marker}")
                    
                    print(f"      Found {posts_found} mystery posts")
                else:
                    print(f"      ⚠️ Status {response.status_code}")
                
                time.sleep(random.uniform(2.0, 4.0))  # Respectful rate limiting
                
            except Exception as e:
                print(f"   ⚠️ Failed to fetch r/{subreddit}: {e}")
                continue
        
        print(f"✅ Found {len(trends)} trending topics from Reddit")
        return trends[:20]
        
    except Exception as e:
        print(f"⚠️ Reddit scraping failed: {e}")
        return []


def clean_reddit_title(title: str) -> str:
    """Clean Reddit post titles for use as video topics"""
    # Remove meta tags
    title = re.sub(r'\[.*?\]', '', title)
    
    # Remove excessive punctuation
    title = re.sub(r'!!!+', '!', title)
    title = re.sub(r'\?\?+', '?', title)
    
    # Remove emojis (we'll add our own)
    title = re.sub(r'[^\w\s\-.,!?\'"():;]', '', title)
    
    # Trim
    title = title.strip()
    
    return title


def get_youtube_mystery_trends() -> List[str]:
    """Scrape trending mystery video topics from YouTube"""
    try:
        print("🔍 Fetching YouTube trending mystery videos...")
        
        # Search for recent viral mystery videos
        search_queries = [
            'unsolved mystery',
            'true crime case',
            'cold case documentary',
            'unexplained disappearance',
            'mysterious discovery',
            'declassified documents',
            'historical mystery',
            'conspiracy theory explained'
        ]
        
        trends = []
        
        for query in search_queries:
            try:
                # Use YouTube search (public, no API needed)
                search_url = f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}&sp=CAMSAhAB"  # sp=CAMSAhAB filters for recent
                
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
                
                print(f"   🎥 Searching: {query}")
                response = requests.get(search_url, headers=headers, timeout=10)
                
                if response.status_code == 200:
                    # Extract video titles using regex (YouTube's JSON embedded in page)
                    title_pattern = r'"title":{"runs":\[{"text":"([^"]+)"}\]'
                    matches = re.findall(title_pattern, response.text)
                    
                    found_count = 0
                    for title in matches[:10]:
                        if is_mystery_title(title) and len(title) > 15:
                            trends.append(title)
                            found_count += 1
                            print(f"      ✓ {title[:70]}")
                    
                    print(f"      Found {found_count} videos")
                
                time.sleep(random.uniform(2.0, 3.0))
                
            except Exception as e:
                print(f"   ⚠️ Failed for '{query}': {e}")
                continue
        
        print(f"✅ Found {len(trends)} trends from YouTube")
        return trends[:15]
        
    except Exception as e:
        print(f"⚠️ YouTube scraping failed: {e}")
        return []


def is_mystery_title(title: str) -> bool:
    """Check if YouTube title is mystery content"""
    title_lower = title.lower()
    
    good_keywords = [
        'mystery', 'unsolved', 'disappear', 'missing', 'strange',
        'unexplained', 'cold case', 'true crime', 'investigation',
        'conspiracy', 'declassified', 'secret', 'hidden',
        'ancient', 'artifact', 'discovery', 'phenomenon'
    ]
    
    bad_keywords = [
        'react', 'reaction', 'review', 'commentary', 'live stream',
        'full podcast', '2 hours', '3 hours', 'compilation',
        'all episodes', 'season', 'trailer', 'teaser'
    ]
    
    has_good = any(kw in title_lower for kw in good_keywords)
    has_bad = any(kw in title_lower for kw in bad_keywords)
    
    return has_good and not has_bad


def get_evergreen_mystery_themes() -> List[str]:
    """Evergreen mystery topics that always perform well"""
    
    current_month = datetime.now().strftime('%B')
    current_hour = datetime.now().hour
    current_day = datetime.now().day
    
    # 🔍 TIME-SPECIFIC EVERGREEN THEMES
    evergreen = []
    
    # Evening prime time themes (7-9 PM)
    if 18 <= current_hour <= 21:
        evergreen.extend([
            "Flight 19: The Bermuda Triangle Mystery That Defies Physics",
            "DB Cooper: The Only Unsolved Airplane Hijacking in History",
            "Malaysia Airlines MH370: The Disappearance That Makes No Sense",
            "The Zodiac Killer: Why His Code Took 51 Years to Crack",
            "The Mary Celeste: Ghost Ship Found With Nobody Aboard"
        ])
    
    # Late night themes (10 PM - 2 AM) - More unsettling
    elif current_hour >= 22 or current_hour <= 2:
        evergreen.extend([
            "The Dyatlov Pass Incident: 9 Hikers Found Dead in Unexplained Circumstances",
            "Elisa Lam: The Elevator Footage That Still Can't Be Explained",
            "The Somerton Man: Dead Body With No Identity and a Secret Code",
            "The Black Dahlia: The Murder That Haunts LA 77 Years Later",
            "The Boy in the Box: America's Unknown Child"
        ])
    
    # General/daytime themes
    else:
        evergreen.extend([
            "The Voynich Manuscript: A Book No One Can Read",
            "The Antikythera Mechanism: 2,000-Year-Old Computer That Shouldn't Exist",
            "Göbekli Tepe: The Temple Built 6,000 Years Before Stonehenge",
            "The Nazca Lines: How Did They Draw These Without Seeing From Above?",
            "The Piri Reis Map: Antarctica Before the Ice?"
        ])
    
    # 🔍 ALWAYS-RELEVANT MYSTERY THEMES
    evergreen.extend([
        # Famous disappearances
        "Amelia Earhart: The Disappearance That Still Baffles Experts",
        "The Lost Colony of Roanoke: 115 People Vanished Overnight",
        "The Philadelphia Experiment: What Really Happened to USS Eldridge?",
        
        # True crime classics
        "Jack the Ripper: Why We Still Don't Know His Identity",
        "The Cleveland Torso Murders: 12 Victims Never Identified",
        "The Axeman of New Orleans: The Serial Killer Who Wrote Letters",
        
        # Conspiracy facts (declassified)
        "MKUltra: CIA Mind Control Experiments Were Real (Declassified Proof)",
        "Operation Northwoods: The False Flag Plan That Was Approved",
        "The Tuskegee Experiment: Medical Conspiracy That Lasted 40 Years",
        
        # Historical enigmas
        "The Baghdad Battery: 2,000-Year-Old Electricity?",
        "The Shroud of Turin: Science Can't Explain the Image",
        "Oak Island Money Pit: The Treasure Hunt That's Killed 6 People",
        
        # Recent mysteries
        "The Wow! Signal: The Space Message We Never Decoded",
        "The Phoenix Lights: Thousands Saw It But Officials Deny It",
        "The Hessdalen Lights: Unexplained Phenomenon Still Happening Today"
    ])
    
    # 🔍 SEASONAL/MONTHLY ADJUSTMENTS
    monthly_themes = {
        'October': [
            "The 13 Most Terrifying Unsolved Mysteries (Halloween Special)",
            "Real Hauntings That Have Documented Evidence",
            "The Most Disturbing Cold Cases Still Open Today"
        ],
        'December': [
            "Mysteries Solved in 2024: What We Finally Learned",
            "The Year's Most Shocking Declassified Documents",
            "2024's Strangest Unsolved Disappearances"
        ],
        'January': [
            "Cold Cases That Might Finally Be Solved in 2024",
            "New Evidence in Old Mysteries: 2024 Updates"
        ]
    }
    
    if current_month in monthly_themes:
        evergreen.extend(monthly_themes[current_month])
    
    # Anniversary-based mysteries (if specific dates)
    if current_month == 'December' and current_day == 5:
        evergreen.insert(0, "Flight 19: Today Marks the Anniversary of the Bermuda Triangle Mystery")
    
    print(f"✅ Loaded {len(evergreen)} evergreen mystery themes (time-optimized)")
    return evergreen


def get_real_mystery_trends() -> List[str]:
    """Combine multiple FREE sources for real mystery trending topics"""
    
    print("\n" + "="*70)
    print("🔍 FETCHING REAL-TIME MYSTERY TRENDS (MULTI-SOURCE)")
    print("="*70)
    
    all_trends = []
    source_counts = {}
    
    # Source 1: Google Trends (mystery-specific)
    try:
        google_trends = get_google_trends_mystery()
        all_trends.extend(google_trends)
        source_counts['Google Trends'] = len(google_trends)
    except Exception as e:
        print(f"⚠️ Google Trends error: {e}")
        source_counts['Google Trends'] = 0
    
    # Source 2: Reddit Mystery Communities
    try:
        reddit_trends = get_reddit_mystery_trends()
        all_trends.extend(reddit_trends)
        source_counts['Reddit'] = len(reddit_trends)
    except Exception as e:
        print(f"⚠️ Reddit error: {e}")
        source_counts['Reddit'] = 0
    
    # Source 3: YouTube Trending
    try:
        youtube_trends = get_youtube_mystery_trends()
        all_trends.extend(youtube_trends)
        source_counts['YouTube'] = len(youtube_trends)
    except Exception as e:
        print(f"⚠️ YouTube error: {e}")
        source_counts['YouTube'] = 0
    
    # Source 4: Evergreen themes (ALWAYS INCLUDED)
    evergreen = get_evergreen_mystery_themes()
    all_trends.extend(evergreen)
    source_counts['Evergreen'] = len(evergreen)
    
    # Deduplicate while preserving order
    seen = set()
    unique_trends = []
    for trend in all_trends:
        trend_clean = trend.lower().strip()
        # Similarity threshold
        is_duplicate = False
        for seen_trend in seen:
            if similar_strings(trend_clean, seen_trend) > 0.8:
                is_duplicate = True
                break
        
        if not is_duplicate and len(trend) > 10:
            seen.add(trend_clean)
            unique_trends.append(trend)
    
    print(f"\n📊 TREND SOURCES SUMMARY:")
    for source, count in source_counts.items():
        print(f"   • {source}: {count} topics")
    print(f"\n   TOTAL UNIQUE: {len(unique_trends)} mystery trends")
    
    return unique_trends[:30]  # Top 30


def similar_strings(s1: str, s2: str) -> float:
    """Calculate similarity between two strings (0-1)"""
    words1 = set(s1.split())
    words2 = set(s2.split())
    
    if not words1 or not words2:
        return 0.0
    
    intersection = len(words1 & words2)
    union = len(words1 | words2)
    
    return intersection / union if union > 0 else 0.0


def filter_and_rank_mystery_trends(trends: List[str], content_type: str) -> List[Dict[str, Any]]:
    """Use Gemini to filter and rank mystery trends for viral potential"""
    
    if not trends:
        print("⚠️ No trends to filter, using fallback...")
        return get_fallback_mystery_ideas(content_type)
    
    print(f"\n🤖 Using Gemini to rank {len(trends)} trends for {content_type} content...")
    
    current_month = datetime.now().strftime('%B')
    current_time = datetime.now().strftime('%I %p')
    current_day = datetime.now().strftime('%A')
    
    # 🔍 CONTENT TYPE SPECIFIC GUIDANCE
    content_type_guidance = {
        'evening_prime': {
            'focus': 'Famous mysteries, high intrigue, accessible stories',
            'emotion': 'Intriguing, mysterious, documentary-style',
            'audience': 'Evening viewers unwinding, ready for intrigue, casual mystery fans'
        },
        'late_night': {
            'focus': 'Darker unsolved cases, disturbing mysteries, unsettling stories',
            'emotion': 'Chilling, serious, thought-provoking, keeps them awake',
            'audience': 'Late night scrollers who can\'t sleep, want something unsettling, deep mystery fans'
        },
        'weekend_binge': {
            'focus': 'Complex layered mysteries, historical enigmas, deep rabbit holes',
            'emotion': 'Documentary deep-dive, detailed, satisfying depth',
            'audience': 'Weekend viewers with time, ready for complexity, true crime enthusiasts'
        },
        'general': {
            'focus': 'Balanced mix of disappearances, crimes, and historical mysteries',
            'emotion': 'Mysterious but accessible, serious but not too dark',
            'audience': 'General mystery enthusiasts, curious viewers, binge-watchers'
        }
    }
    
    guidance = content_type_guidance.get(content_type, content_type_guidance['general'])
    
    prompt = f"""You are a viral mystery content strategist analyzing REAL trending topics for YouTube Shorts.

REAL TRENDING MYSTERY TOPICS (from Google/Reddit/YouTube/Evergreen):
{chr(10).join(f"{i+1}. {t}" for i, t in enumerate(trends[:30]))}

CURRENT CONTEXT:
- Day: {current_day}
- Month: {current_month}
- Time: {current_time}
- Content Type: {content_type}
- Target Focus: {guidance['focus']}
- Emotional Tone: {guidance['emotion']}
- Target Audience: {guidance['audience']}

TASK: Select TOP 5 mystery topics that would make MOST VIRAL YouTube Shorts for the {content_type} time slot.

SELECTION CRITERIA (in order of importance):
1. **Intrigue Factor**: Must create "I NEED to know what happened" feeling
2. **Story Completeness**: Must fit in 60-90 seconds but feel complete
3. **Shareability**: Must make people send to friends who love mysteries
4. **Unanswered Question**: Must leave viewers wanting to discuss/theorize
5. **Time Relevance**: Must fit {content_type} audience mood
6. **Specific Mystery**: Prefer specific cases over vague mysteries
7. **Binge Potential**: Must make them watch next video immediately

GOOD EXAMPLES FOR {content_type}:
{get_example_mystery_titles_for_content_type(content_type)}

AVOID:
- Mysteries requiring too much context (can't explain in 60s)
- Overly graphic true crime (focus on mystery not gore)
- Unverified conspiracy theories
- Active missing persons cases (ethical concern)
- Mysteries already covered extensively (unless new angle)

OUTPUT (JSON only):
{{
  "selected_topics": [
    {{
      "title": "Specific viral mystery title optimized for {content_type}",
      "reason": "Why this mystery will go viral for {guidance['audience']}",
      "viral_score": 95,
      "hook_angle": "Specific impossible detail to hook viewers",
      "mystery_type": "disappearance/crime/historical/conspiracy",
      "key_contradiction": "The fact that doesn't make sense"
    }}
  ]
}}

Select 5 mysteries ranked by viral_score (highest first). Make them DIFFERENT categories from each other."""

    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = model.generate_content(prompt)
            result_text = response.text.strip()
            
            # Extract JSON
            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', result_text, re.DOTALL)
            if json_match:
                result_text = json_match.group(1)
            else:
                json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
                if json_match:
                    result_text = json_match.group(0)
            
            data = json.loads(result_text)
            
            trending_ideas = []
            for item in data.get('selected_topics', [])[:5]:
                trending_ideas.append({
                    "topic_title": item.get('title', 'Unknown'),
                    "summary": item.get('reason', 'High viral potential'),
                    "category": item.get('mystery_type', 'mystery'),
                    "viral_score": item.get('viral_score', 90),
                    "hook_angle": item.get('hook_angle', 'Impossible event'),
                    "key_contradiction": item.get('key_contradiction', 'Unexplained detail'),
                    "content_type": content_type
                })
            
            print(f"✅ Gemini ranked {len(trending_ideas)} viral mysteries")
            for i, idea in enumerate(trending_ideas, 1):
                print(f"   {i}. [{idea['viral_score']}] {idea['topic_title'][:60]}")
            
            return trending_ideas
            
        except Exception as e:
            print(f"❌ Attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
    
    print("⚠️ Gemini ranking failed, using fallback...")
    return get_fallback_mystery_ideas(content_type)


def get_example_mystery_titles_for_content_type(content_type: str) -> str:
    """Get example titles for each content type"""
    examples = {
        'evening_prime': """
- "Flight 19: Five Planes Vanished, Zero Evidence Ever Found"
- "DB Cooper: The Only Unsolved Hijacking in US History"
- "Malaysia MH370: The Disappearance That Defies All Logic"
- "The Zodiac Killer: Why His Code Took 51 Years to Crack"
""",
        'late_night': """
- "The Dyatlov Pass: 9 Hikers Found Dead in Impossible Circumstances"
- "Elisa Lam: The Elevator Footage Nobody Can Explain"
- "The Somerton Man: Dead Body, No Identity, Secret Code"
- "The Boy in the Box: America's Unknown Child (Still Unsolved)"
""",
        'weekend_binge': """
- "The Voynich Manuscript: A 600-Year-Old Book No One Can Read"
- "Antikythera Mechanism: Ancient Computer That Shouldn't Exist"
- "Göbekli Tepe: The Temple That Rewrites Human History"
- "The Piri Reis Map: How Did They Map Antarctica Before the Ice?"
"""
    }
    return examples.get(content_type, examples['evening_prime'])


def get_fallback_mystery_ideas(content_type: str) -> List[Dict[str, Any]]:
    """Fallback mystery ideas if all methods fail"""
    
    fallbacks = {
        'evening_prime': [
            {
                "topic_title": "Flight 19: The Bermuda Triangle Mystery That Defies Physics",
                "summary": "Famous disappearance with zero evidence - perfect evening hook",
                "category": "disappearance",
                "viral_score": 95,
                "hook_angle": "Five planes vanished, rescue plane also disappeared same night",
                "key_contradiction": "No wreckage despite largest search in history",
                "content_type": "evening_prime"
            },
            {
                "topic_title": "DB Cooper: America's Only Unsolved Airplane Hijacking",
                "summary": "Daring escape mystery that captivates audiences",
                "category": "disappearance",
                "viral_score": 93,
                "hook_angle": "Jumped from plane with $200K and vanished forever",
                "key_contradiction": "Survived impossible jump in business suit",
                "content_type": "evening_prime"
            }
        ],
        'late_night': [
            {
                "topic_title": "The Dyatlov Pass Incident: 9 Hikers Dead in Unexplained Circumstances",
                "summary": "Disturbing unsolved mystery perfect for late night audience",
                "category": "crime",
                "viral_score": 96,
                "hook_angle": "Tent ripped from inside, bodies found in impossible conditions",
                "key_contradiction": "Radiation on clothes, missing tongues, no attackers",
                "content_type": "late_night"
            },
            {
                "topic_title": "Elisa Lam: The Elevator Footage That Still Can't Be Explained",
                "summary": "Eerie footage and impossible death location",
                "category": "crime",
                "viral_score": 94,
                "hook_angle": "Found in locked water tank on hotel roof",
                "key_contradiction": "How did she get inside sealed tank from outside?",
                "content_type": "late_night"
            }
        ],
        'weekend_binge': [
            {
                "topic_title": "The Voynich Manuscript: A Book No One Can Read for 600 Years",
                "summary": "Complex historical mystery for weekend deep dive",
                "category": "historical",
                "viral_score": 91,
                "hook_angle": "Unknown language, impossible plants, indecipherable",
                "key_contradiction": "Too complex to be hoax, too strange to be real",
                "content_type": "weekend_binge"
            }
        ]
    }
    
    # Get content-type specific fallbacks
    ideas = fallbacks.get(content_type, fallbacks['evening_prime'])
    
    print(f"📋 Using {len(ideas)} fallback mystery ideas for {content_type}")
    return ideas


def save_trending_data(trending_ideas: List[Dict[str, Any]], content_type: str):
    """Save trending data to file"""
    
    trending_data = {
        "topics": [idea["topic_title"] for idea in trending_ideas],
        "full_data": trending_ideas,
        "generated_at": datetime.now().isoformat(),
        "timestamp": time.time(),
        "content_type": content_type,
        "niche": "mystery",  # Changed from "motivation"
        "source": "google_trends + reddit + youtube + evergreen + gemini_ranking",
        "version": "2.0_mystery"  # Changed from "2.0_robust"
    }
    
    trending_file = os.path.join(TMP, "trending.json")
    with open(trending_file, "w", encoding="utf-8") as f:
        json.dump(trending_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Saved trending data to: {trending_file}")
    return trending_file


if __name__ == "__main__":
    
    # Get content type from environment (set by workflow)
    content_type = os.getenv('CONTENT_TYPE', 'evening_prime')  # Changed default
    mystery_type = os.getenv('MYSTERY_TYPE', 'auto')  # Changed from intensity
    
    print(f"\n🎯 TARGET: {content_type} content with {mystery_type} mystery type")
    
    # Get real trending mystery topics
    real_trends = get_real_mystery_trends()
    
    if real_trends:
        # Use Gemini to filter and rank
        trending_ideas = filter_and_rank_mystery_trends(real_trends, content_type)
    else:
        print("⚠️ Could not fetch real trends, using fallback...")
        trending_ideas = get_fallback_mystery_ideas(content_type)
    
    if trending_ideas:
        print(f"\n" + "="*70)
        print(f"🔍 TOP VIRAL MYSTERY IDEAS FOR {content_type.upper()}")
        print("="*70)
        
        for i, idea in enumerate(trending_ideas, 1):
            print(f"\n💎 MYSTERY {i}:")
            print(f"   Title: {idea['topic_title']}")
            print(f"   Type: {idea.get('category', 'mystery')}")
            print(f"   Viral Score: {idea.get('viral_score', 'N/A')}/100")
            print(f"   Hook: {idea.get('hook_angle', 'N/A')}")
            print(f"   Contradiction: {idea.get('key_contradiction', 'N/A')}")
            print(f"   Why: {idea['summary'][:100]}...")
        
        # Save to file
        save_trending_data(trending_ideas, content_type)
        
        print(f"\n✅ TRENDING DATA READY FOR SCRIPT GENERATION")
        print(f"   Sources: Multi-platform real-time data")
        print(f"   Quality: Gemini-filtered for viral potential")
        print(f"   Optimized: {content_type} audience")
        
    else:
        print("\n❌ Could not retrieve any trending ideas.")
        exit(1)