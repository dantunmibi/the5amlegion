#!/usr/bin/env python3
"""
🔥 Fetch Trending Motivational Topics - ROBUST VERSION
Multi-source trending data collector for motivation niche
Sources: Google Trends, Reddit, YouTube, Evergreen motivational themes
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

# Model selection (same as reference)
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


def get_google_trends_motivation() -> List[str]:
    """Get real trending motivational searches from Google Trends"""
    try:
        from pytrends.request import TrendReq
        
        print(f"🔥 Fetching Google Trends (Motivation & Discipline)...")
        
        try:
            pytrends = TrendReq(hl='en-US', tz=360, timeout=(10, 25))
        except Exception as init_error:
            print(f"   ⚠️ PyTrends initialization failed: {init_error}")
            return []
        
        relevant_trends = []
        
        # 🔥 MOTIVATION-SPECIFIC KEYWORDS
        motivational_topics = [
            # Core motivation
            'motivation quotes',
            'daily motivation', 
            'morning motivation',
            
            # Discipline & habits
            'discipline',
            '5am club',
            'morning routine',
            'waking up early',
            
            # Success & mindset
            'success mindset',
            'mental toughness',
            'growth mindset',
            'self improvement',
            
            # Influencers (trending)
            'david goggins',
            'jocko willink',
            'andrew huberman',
            'jordan peterson motivation',
            
            # Actionable
            'how to be disciplined',
            'how to stop procrastinating',
            'how to wake up at 5am',
            'how to build habits'
        ]
        
        for topic in motivational_topics:
            try:
                print(f"   🔍 Searching trends for: {topic}")
                pytrends.build_payload([topic], timeframe='now 7-d', geo='US')
                
                # Get related queries
                related = pytrends.related_queries()
                
                if topic in related and 'top' in related[topic]:
                    top_queries = related[topic]['top']
                    if top_queries is not None and not top_queries.empty:
                        for query in top_queries['query'].head(5):
                            # Filter for motivational relevance
                            if len(query) > 10 and is_motivational_query(query):
                                relevant_trends.append(query)
                                print(f"      ✓ {query}")
                
                # Also check rising queries (viral potential)
                if topic in related and 'rising' in related[topic]:
                    rising_queries = related[topic]['rising']
                    if rising_queries is not None and not rising_queries.empty:
                        for query in rising_queries['query'].head(3):
                            if len(query) > 10 and is_motivational_query(query):
                                relevant_trends.append(f"{query} (🔥 RISING)")
                                print(f"      🔥 {query} (RISING)")
                
                time.sleep(random.uniform(1.5, 3.0))  # Respectful rate limiting
                
            except Exception as e:
                print(f"   ⚠️ Failed for '{topic}': {str(e)[:50]}...")
                continue
        
        print(f"✅ Found {len(relevant_trends)} motivational trends from Google")
        return relevant_trends[:20]
        
    except ImportError:
        print("⚠️ pytrends not installed - skipping Google Trends")
        print("   Install with: pip install pytrends")
        return []
    except Exception as e:
        print(f"⚠️ Google Trends failed: {e}")
        return []


def is_motivational_query(query: str) -> bool:
    """Filter for motivational relevance"""
    query_lower = query.lower()
    
    # Good motivational keywords
    good_keywords = [
        'motivation', 'discipline', 'mindset', 'success', 'habit',
        'routine', 'morning', '5am', 'wake up', 'productivity',
        'self improvement', 'mental', 'tough', 'grind', 'hustle',
        'goal', 'achievement', 'winner', 'champion', 'transform',
        'goggins', 'jocko', 'peterson', 'huberman'
    ]
    
    # Avoid non-motivational topics
    bad_keywords = [
        'song', 'music', 'movie', 'trailer', 'meme', 'funny',
        'game', 'anime', 'celebrity', 'news', 'politics',
        'price', 'buy', 'shop', 'sale'
    ]
    
    has_good = any(kw in query_lower for kw in good_keywords)
    has_bad = any(kw in query_lower for kw in bad_keywords)
    
    return has_good and not has_bad


def get_reddit_motivation_trends() -> List[str]:
    """Get trending posts from motivational subreddits"""
    try:
        print("🔥 Fetching Reddit motivation trends...")
        
        # 🔥 MOTIVATION-SPECIFIC SUBREDDITS
        subreddits = [
            'GetMotivated',      # 20M+ members
            'GetDisciplined',    # 1M+ members
            'selfimprovement',   # 800K+ members
            'DecidingToBeBetter',# 300K+ members
            'productivity',      # 200K+ members
            'NonZeroDay',        # Accountability
            'motivation',        # General motivation
            'DisciplineAndGrit'  # Hardcore discipline
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
                        
                        # 🔥 MOTIVATION-SPECIFIC FILTERING
                        good_phrases = [
                            # Actionable
                            'how i', 'how to', 'this changed', 'stopped', 'started',
                            'i finally', 'after years', 'my journey',
                            
                            # Discipline themes
                            'discipline', 'routine', 'habit', 'consistency',
                            'wake up', 'morning', '5am', 'early',
                            
                            # Mindset themes
                            'mindset', 'focus', 'mental', 'overcame',
                            'transformation', 'changed my life',
                            
                            # Advice/tips
                            'tip', 'advice', 'strategy', 'method',
                            'secret', 'truth', 'lesson', 'learned'
                        ]
                        
                        # Reject vague/unhelpful posts
                        bad_phrases = [
                            'should i', 'can someone', 'need help', 'feeling lost',
                            'what do', 'how do i start', 'depressed', 'suicide',
                            'rant', 'venting', 'anybody else', 'dae',
                            'am i the only', 'unpopular opinion'
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
                    
                    print(f"      Found {posts_found} motivational posts")
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


def get_youtube_motivation_trends() -> List[str]:
    """Scrape trending motivational video topics from YouTube"""
    try:
        print("🔥 Fetching YouTube trending motivational videos...")
        
        # Search for recent viral motivational videos
        search_queries = [
            'motivational speech',
            'morning routine 5am',
            'discipline motivation',
            'david goggins motivation',
            'success mindset'
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
                        if is_motivational_title(title) and len(title) > 15:
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


def is_motivational_title(title: str) -> bool:
    """Check if YouTube title is motivational content"""
    title_lower = title.lower()
    
    good_keywords = [
        'motivation', 'discipline', 'wake up', '5am', 'morning',
        'success', 'mindset', 'transform', 'change your life',
        'routine', 'habit', 'goggins', 'jocko', 'speech'
    ]
    
    bad_keywords = [
        'react', 'reaction', 'review', 'analysis', 'breakdown',
        'full podcast', 'interview', 'compilation', 'playlist'
    ]
    
    has_good = any(kw in title_lower for kw in good_keywords)
    has_bad = any(kw in title_lower for kw in bad_keywords)
    
    return has_good and not has_bad


def get_evergreen_motivational_themes() -> List[str]:
    """Evergreen motivational topics that always perform well"""
    
    current_month = datetime.now().strftime('%B')
    current_hour = datetime.now().hour
    
    # 🔥 TIME-SPECIFIC EVERGREEN THEMES
    evergreen = []
    
    # Morning themes (4-10 AM)
    if 4 <= current_hour <= 10:
        evergreen.extend([
            "Why Successful People Wake Up at 5 AM (The Morning Advantage)",
            "The First Hour of Your Day Determines Everything",
            "Stop Hitting Snooze: The Discipline That Changes Lives",
            "What Champions Do Before 6 AM (Morning Routine Secrets)",
            "Your Morning Routine Is Your Life Routine"
        ])
    
    # Late night themes (10 PM - 3 AM)
    elif current_hour >= 22 or current_hour <= 3:
        evergreen.extend([
            "Reading This at 2 AM? Here's What You Need to Hear",
            "You Can't Sleep Because You Know You're Wasting Time",
            "Tomorrow Starts Tonight: Set Your Alarm for 5 AM Now",
            "The 2 AM Truth: Your Future Self Is Watching",
            "Stop Scrolling Start Living: The Late Night Wake-Up Call"
        ])
    
    # Daytime themes (general)
    else:
        evergreen.extend([
            "Stop Making Excuses and Start Making Progress",
            "Nobody's Coming to Save You (So Save Yourself)",
            "Your Comfort Zone Is Killing Your Dreams",
            "The Brutal Truth About Overnight Success",
            "Why Hard Work Will Always Beat Talent"
        ])
    
    # 🔥 ALWAYS-RELEVANT MOTIVATIONAL THEMES
    evergreen.extend([
        "You're Not Tired You're Undisciplined (Wake Up Call)",
        "Discipline Beats Motivation Every Single Time",
        "While You Sleep They Grind: The Success Formula",
        "Stop Negotiating With Yourself: Just Do It Anyway",
        "The Old You Dies Today (Identity Transformation)",
        "How to Build Unbreakable Mental Toughness",
        "The Difference Between Winners and Losers",
        "What You Do When You Don't Feel Like It Defines You",
        "Your Excuses Are Valid But They're Keeping You Broke",
        "The 1% Rule: How Small Actions Create Big Results"
    ])
    
    # 🔥 SEASONAL/MONTHLY ADJUSTMENTS
    monthly_themes = {
        'January': [
            "New Year Same Excuses? Not This Time (2024 Discipline)",
            "How to Actually Keep Your New Year's Resolutions",
            "January 1st vs January 31st: The Discipline Gap"
        ],
        'September': [
            "Back to School Back to Grind: Student Success Mindset",
            "Fall Season Fall Into Discipline (Autumn Motivation)"
        ],
        'December': [
            "Finish The Year Strong: December Discipline",
            "New Year New You Starts Now (December Prep)"
        ]
    }
    
    if current_month in monthly_themes:
        evergreen.extend(monthly_themes[current_month])
    
    print(f"✅ Loaded {len(evergreen)} evergreen motivational themes (time-optimized)")
    return evergreen


def get_real_motivational_trends() -> List[str]:
    """Combine multiple FREE sources for real motivational trending topics"""
    
    print("\n" + "="*70)
    print("🔥 FETCHING REAL-TIME MOTIVATIONAL TRENDS (MULTI-SOURCE)")
    print("="*70)
    
    all_trends = []
    source_counts = {}
    
    # Source 1: Google Trends (motivation-specific)
    try:
        google_trends = get_google_trends_motivation()
        all_trends.extend(google_trends)
        source_counts['Google Trends'] = len(google_trends)
    except Exception as e:
        print(f"⚠️ Google Trends error: {e}")
        source_counts['Google Trends'] = 0
    
    # Source 2: Reddit Motivation Communities
    try:
        reddit_trends = get_reddit_motivation_trends()
        all_trends.extend(reddit_trends)
        source_counts['Reddit'] = len(reddit_trends)
    except Exception as e:
        print(f"⚠️ Reddit error: {e}")
        source_counts['Reddit'] = 0
    
    # Source 3: YouTube Trending
    try:
        youtube_trends = get_youtube_motivation_trends()
        all_trends.extend(youtube_trends)
        source_counts['YouTube'] = len(youtube_trends)
    except Exception as e:
        print(f"⚠️ YouTube error: {e}")
        source_counts['YouTube'] = 0
    
    # Source 4: Evergreen themes (ALWAYS INCLUDED)
    evergreen = get_evergreen_motivational_themes()
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
    print(f"\n   TOTAL UNIQUE: {len(unique_trends)} motivational trends")
    
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


def filter_and_rank_motivational_trends(trends: List[str], content_type: str) -> List[Dict[str, Any]]:
    """Use Gemini to filter and rank motivational trends for viral potential"""
    
    if not trends:
        print("⚠️ No trends to filter, using fallback...")
        return get_fallback_motivational_ideas(content_type)
    
    print(f"\n🤖 Using Gemini to rank {len(trends)} trends for {content_type} content...")
    
    current_month = datetime.now().strftime('%B')
    current_time = datetime.now().strftime('%I %p')
    current_day = datetime.now().strftime('%A')
    
    # 🔥 CONTENT TYPE SPECIFIC GUIDANCE
    content_type_guidance = {
        'early_morning': {
            'focus': '5 AM wake-ups, morning routines, discipline over comfort',
            'emotion': 'Aggressive, commanding, military-style motivation',
            'audience': 'Early risers, discipline seekers, 5 AM warriors'
        },
        'late_night': {
            'focus': '2 AM accountability, guilt about wasted day, tomorrow starts now',
            'emotion': 'Intimate, honest, brother-to-brother real talk',
            'audience': 'Late night scrollers, people with regret, insomniacs questioning life'
        },
        'midday': {
            'focus': 'No excuses grind, push through afternoon slump, keep going',
            'emotion': 'Urgent, no-nonsense, direct commands',
            'audience': 'Procrastinators, midday break scrollers, people losing momentum'
        },
        'evening': {
            'focus': 'Daily reflection, what did you accomplish, prepare for tomorrow',
            'emotion': 'Reflective but powerful, accountability-focused',
            'audience': 'Evening planners, people reviewing their day, goal-setters'
        },
        'general': {
            'focus': 'Discipline, mindset shifts, success principles',
            'emotion': 'Balanced intensity, inspirational but firm',
            'audience': 'General motivation seekers, self-improvement enthusiasts'
        }
    }
    
    guidance = content_type_guidance.get(content_type, content_type_guidance['general'])
    
    prompt = f"""You are a viral motivational content strategist analyzing REAL trending topics.

REAL TRENDING MOTIVATIONAL TOPICS (from Google/Reddit/YouTube/Evergreen):
{chr(10).join(f"{i+1}. {t}" for i, t in enumerate(trends[:30]))}

CURRENT CONTEXT:
- Day: {current_day}
- Month: {current_month}
- Time: {current_time}
- Content Type: {content_type}
- Target Focus: {guidance['focus']}
- Emotional Tone: {guidance['emotion']}
- Target Audience: {guidance['audience']}

TASK: Select TOP 5 topics that would make MOST VIRAL YouTube Shorts for the {content_type} time slot.

SELECTION CRITERIA (in order of importance):
1. **Emotional Impact**: Must hit deep pain points (wasted potential, fear, regret)
2. **Immediate Action**: Must have clear "do this RIGHT NOW" moment
3. **Identity Shift**: Must show transformation from old self to new self
4. **Share Potential**: Must make people tag friends who need this
5. **Time Relevance**: Must fit {content_type} audience state
6. **Specificity**: Prefer specific actions over vague advice
7. **Urgency**: Must create "I need to change NOW" feeling

GOOD EXAMPLES FOR {content_type}:
{get_example_titles_for_content_type(content_type)}

OUTPUT (JSON only):
{{
  "selected_topics": [
    {{
      "title": "Specific viral title optimized for {content_type}",
      "reason": "Why this will go viral for {guidance['audience']}",
      "viral_score": 95,
      "hook_angle": "Specific emotional hook to use",
      "target_pain": "Exact pain point this addresses",
      "cta_idea": "What immediate action to command"
    }}
  ]
}}

Select 5 topics ranked by viral_score (highest first). Make them DIFFERENT from each other."""

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
                    "category": "Motivation",
                    "viral_score": item.get('viral_score', 90),
                    "hook_angle": item.get('hook_angle', 'Brutal honest opening'),
                    "target_pain": item.get('target_pain', 'Wasted potential'),
                    "cta_idea": item.get('cta_idea', 'Take action now'),
                    "content_type": content_type
                })
            
            print(f"✅ Gemini ranked {len(trending_ideas)} viral topics")
            for i, idea in enumerate(trending_ideas, 1):
                print(f"   {i}. [{idea['viral_score']}] {idea['topic_title'][:60]}")
            
            return trending_ideas
            
        except Exception as e:
            print(f"❌ Attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
    
    print("⚠️ Gemini ranking failed, using fallback...")
    return get_fallback_motivational_ideas(content_type)


def get_example_titles_for_content_type(content_type: str) -> str:
    """Get example titles for each content type"""
    examples = {
        'early_morning': """
- "5 AM OR STAY BROKE: Your Choice (Morning Discipline)"
- "What Successful People Do Before 6 AM (You're Sleeping)"
- "Stop Hitting Snooze: The 5 Second Rule That Changes Everything"
""",
        'late_night': """
- "Reading This at 2 AM? Here's Why You Can't Sleep (Truth)"
- "You Wasted Today: Tomorrow Starts Right Now (Set Alarm)"
- "The 2 AM Accountability: Your Future Self Is Watching"
""",
        'midday': """
- "It's 2 PM: What Have You Actually Accomplished Today?"
- "Stop Scrolling Start Doing: The Midday Reality Check"
- "No Excuses: Get Back to Work Right Now (No Tomorrow)"
""",
        'evening': """
- "End of Day: Did You Win or Just Survive? (Reflection)"
- "Tomorrow Starts Tonight: Plan Your Morning Attack Now"
- "What Did You Build Today? (Evening Accountability Check)"
"""
    }
    return examples.get(content_type, examples['midday'])


def get_fallback_motivational_ideas(content_type: str) -> List[Dict[str, Any]]:
    """Fallback motivational ideas if all methods fail"""
    
    fallbacks = {
        'early_morning': [
            {
                "topic_title": "YOU'RE NOT TIRED YOU'RE UNDISCIPLINED (5 AM Wake-Up)",
                "summary": "Brutal truth about hitting snooze vs waking up at 5 AM like champions",
                "category": "Morning Fire",
                "viral_score": 95,
                "hook_angle": "You slept 8 hours so what's the real problem",
                "target_pain": "Lack of discipline disguised as tiredness",
                "cta_idea": "Set alarm for 5 AM right now, no negotiation",
                "content_type": "early_morning"
            },
            {
                "topic_title": "THE FIRST HOUR OWNS THE DAY (Morning Routine Secrets)",
                "summary": "Why your morning routine determines everything that follows",
                "category": "Morning Fire",
                "viral_score": 92,
                "hook_angle": "Winners own their morning, losers let morning own them",
                "target_pain": "Chaotic mornings leading to chaotic days",
                "cta_idea": "Write down your morning routine tonight",
                "content_type": "early_morning"
            }
        ],
        'late_night': [
            {
                "topic_title": "READING THIS AT 2 AM? Here's The Truth You Need",
                "summary": "Why late night scrollers can't sleep (guilt about wasted day)",
                "category": "Late Night Accountability",
                "viral_score": 96,
                "hook_angle": "You can't sleep because you know you wasted today",
                "target_pain": "Regret about procrastination and unfulfilled potential",
                "cta_idea": "Set alarm for 5 AM tomorrow starts now",
                "content_type": "late_night"
            },
            {
                "topic_title": "YOUR FUTURE SELF IS WATCHING (The 2 AM Decision)",
                "summary": "Tomorrow is decided tonight - make the choice that changes everything",
                "category": "Late Night Accountability",
                "viral_score": 94,
                "hook_angle": "Every night you choose tomorrow's outcome",
                "target_pain": "Repeated cycle of wasted days",
                "cta_idea": "Close app and plan tomorrow right now",
                "content_type": "late_night"
            }
        ],
        'midday': [
            {
                "topic_title": "NOBODY'S COMING TO SAVE YOU (Save Yourself)",
                "summary": "Stop waiting for motivation, permission, or the perfect moment",
                "category": "Discipline & Grind",
                "viral_score": 93,
                "hook_angle": "You're waiting for someone to rescue you but nobody's coming",
                "target_pain": "Waiting for external validation to start",
                "cta_idea": "Do one thing right now, anything, just move",
                "content_type": "midday"
            }
        ],
        'evening': [
            {
                "topic_title": "WHAT DID YOU BUILD TODAY? (Evening Reflection)",
                "summary": "Honest accountability about how you spent your 24 hours",
                "category": "Mindset Shift",
                "viral_score": 91,
                "hook_angle": "Today's almost over - did you win or make excuses",
                "target_pain": "Busy but not productive, motion without progress",
                "cta_idea": "Review today and plan tomorrow before sleep",
                "content_type": "evening"
            }
        ]
    }
    
    # Get content-type specific fallbacks, or use general
    ideas = fallbacks.get(content_type, fallbacks['midday'])
    
    print(f"📋 Using {len(ideas)} fallback ideas for {content_type}")
    return ideas


def save_trending_data(trending_ideas: List[Dict[str, Any]], content_type: str):
    """Save trending data to file"""
    
    trending_data = {
        "topics": [idea["topic_title"] for idea in trending_ideas],
        "full_data": trending_ideas,
        "generated_at": datetime.now().isoformat(),
        "timestamp": time.time(),
        "content_type": content_type,
        "niche": "motivation",
        "source": "google_trends + reddit + youtube + evergreen + gemini_ranking",
        "version": "2.0_robust"
    }
    
    trending_file = os.path.join(TMP, "trending.json")
    with open(trending_file, "w", encoding="utf-8") as f:
        json.dump(trending_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Saved trending data to: {trending_file}")
    return trending_file


if __name__ == "__main__":
    
    # Get content type from environment (set by workflow)
    content_type = os.getenv('CONTENT_TYPE', 'general')
    intensity = os.getenv('INTENSITY', 'balanced')
    
    print(f"\n🎯 TARGET: {content_type} content with {intensity} intensity")
    
    # Get real trending motivational topics
    real_trends = get_real_motivational_trends()
    
    if real_trends:
        # Use Gemini to filter and rank
        trending_ideas = filter_and_rank_motivational_trends(real_trends, content_type)
    else:
        print("⚠️ Could not fetch real trends, using fallback...")
        trending_ideas = get_fallback_motivational_ideas(content_type)
    
    if trending_ideas:
        print(f"\n" + "="*70)
        print(f"🔥 TOP VIRAL MOTIVATIONAL IDEAS FOR {content_type.upper()}")
        print("="*70)
        
        for i, idea in enumerate(trending_ideas, 1):
            print(f"\n💎 IDEA {i}:")
            print(f"   Title: {idea['topic_title']}")
            print(f"   Viral Score: {idea.get('viral_score', 'N/A')}/100")
            print(f"   Hook: {idea.get('hook_angle', 'N/A')}")
            print(f"   Pain Point: {idea.get('target_pain', 'N/A')}")
            print(f"   CTA: {idea.get('cta_idea', 'N/A')}")
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