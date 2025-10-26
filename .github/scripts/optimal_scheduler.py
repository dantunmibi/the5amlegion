#!/usr/bin/env python3
"""
🔥 THE 5AM LEGION - Optimal Posting Scheduler
Targets 2AM scrollers, 5AM warriors, and evening reflectors
NOW SUPPORTS WAT (West Africa Time)
"""

import os
import json
import sys
from datetime import datetime, timedelta
import pytz

# MASTER SCHEDULE - Now supports BOTH EST and WAT
TIMEZONE = os.getenv("SCHEDULER_TIMEZONE", "Africa/Lagos")  # WAT by default

# Motivation content performs best at these times:
OPTIMAL_SCHEDULE = {
    # Monday: Start strong
    0: {
        "times": [5, 12, 23],  # 5 AM, 12 PM, 11 PM
        "content_types": ["morning_fire", "midday_boost", "late_night_accountability"],
        "priority": ["highest", "medium", "extreme"]
    },
    # Tuesday: Triple threat
    1: {
        "times": [6, 14, 22],  # 6 AM, 2 PM, 10 PM
        "content_types": ["discipline", "afternoon_push", "evening_reflection"],
        "priority": ["highest", "medium", "high"]
    },
    # Wednesday: Mid-week motivation
    2: {
        "times": [5, 18, 23],  # 5 AM, 6 PM, 11 PM
        "content_types": ["morning_fire", "evening_fire", "late_scrollers"],
        "priority": ["highest", "high", "extreme"]
    },
    # Thursday: Include 2AM slot (VIRAL TIME)
    3: {
        "times": [2, 6, 13, 22],  # 2 AM, 6 AM, 1 PM, 10 PM
        "content_types": ["late_night_truth", "discipline", "midday_fire", "night_warriors"],
        "priority": ["extreme", "highest", "medium", "high"]
    },
    # Friday: Weekend prep
    4: {
        "times": [5, 19, 23],  # 5 AM, 7 PM, 11 PM
        "content_types": ["morning_fire", "weekend_prep", "friday_reflection"],
        "priority": ["highest", "high", "high"]
    },
    # Saturday: No days off
    5: {
        "times": [7, 14, 22],  # 7 AM, 2 PM, 10 PM
        "content_types": ["weekend_grind", "afternoon_inspiration", "reflection"],
        "priority": ["high", "medium", "high"]
    },
    # Sunday: Quad threat (including Sunday night anxiety)
    6: {
        "times": [6, 8, 21, 1],  # 6 AM, 8 AM, 9 PM, 1 AM
        "content_types": ["early_riser", "sunday_motivation", "week_prep", "sunday_crisis"],
        "priority": ["highest", "high", "high", "extreme"]
    }
}

# Content pillar mapping
CONTENT_PILLARS = {
    "morning_fire": {
        "percentage": 30,
        "description": "Aggressive wake-up calls, 5AM warrior content",
        "emotional_tone": "intense",
        "visual_style": "sunrise, training, warrior",
        "keywords": ["wake up", "5am", "grind", "warrior", "discipline"]
    },
    "discipline": {
        "percentage": 25,
        "description": "Hard work, no excuses, relentless grind",
        "emotional_tone": "commanding",
        "visual_style": "training montages, struggle, victory",
        "keywords": ["discipline", "focus", "commitment", "relentless", "grind"]
    },
    "mindset_shift": {
        "percentage": 20,
        "description": "Reframe failure, change beliefs, mental toughness",
        "emotional_tone": "contemplative_powerful",
        "visual_style": "reflective, journey, transformation",
        "keywords": ["mindset", "belief", "transform", "perspective", "strength"]
    },
    "late_night_accountability": {
        "percentage": 15,
        "description": "2AM scrollers, existential crisis, late night truth",
        "emotional_tone": "intimate_honest",
        "visual_style": "dark, alone, city at night",
        "keywords": ["truth", "real", "honest", "late night", "accountability"]
    },
    "success_stories": {
        "percentage": 10,
        "description": "Transformation proof, it's possible, inspiration",
        "emotional_tone": "aspirational",
        "visual_style": "before/after, celebration, achievement",
        "keywords": ["possible", "achieved", "transformation", "proof", "success"]
    },
    "afternoon_push": {
        "percentage": 15,
        "description": "Afternoon motivation boost, fight the slump",
        "emotional_tone": "energetic",
        "visual_style": "action, momentum, power",
        "keywords": ["energy", "push", "afternoon", "momentum", "continue"]
    },
    "evening_reflection": {
        "percentage": 15,
        "description": "Evening reflection, day review, tomorrow prep",
        "emotional_tone": "contemplative",
        "visual_style": "sunset, reflection, planning",
        "keywords": ["reflect", "review", "tomorrow", "prepare", "vision"]
    },
    "weekend_grind": {
        "percentage": 15,
        "description": "Weekend warriors, no excuses on weekends",
        "emotional_tone": "determined",
        "visual_style": "weekend activities, commitment, passion",
        "keywords": ["weekend", "warrior", "committed", "passion", "no excuses"]
    },
    "week_prep": {
        "percentage": 15,
        "description": "Prepare for the upcoming week, set intentions",
        "emotional_tone": "hopeful_determined",
        "visual_style": "planning, vision, future",
        "keywords": ["week ahead", "prepare", "goals", "vision", "ready"]
    }
}

def get_current_time(tz_name=TIMEZONE):
    """Get current time in specified timezone"""
    tz = pytz.timezone(tz_name)
    return datetime.now(tz)

def should_post_now(ignore_schedule=False):
    """Determine if current time is optimal for posting"""
    current = get_current_time()
    weekday = current.weekday()
    hour = current.hour
    
    if ignore_schedule:
        return True, "manual", "user_triggered", current
    
    if weekday not in OPTIMAL_SCHEDULE:
        return False, "low", "off_schedule", current
    
    schedule = OPTIMAL_SCHEDULE[weekday]
    times = schedule["times"]
    
    # Check if within 30 minutes of optimal time
    for idx, optimal_hour in enumerate(times):
        time_diff = abs(hour - optimal_hour)
        if time_diff <= 0.5:  # Within 30 minutes
            content_type = schedule["content_types"][idx]
            priority = schedule["priority"][idx]
            return True, priority, content_type, current
    
    return False, "low", "off_schedule", current

def get_next_optimal_slot():
    """Get the next optimal posting time"""
    current = get_current_time()
    
    # Check all upcoming slots in the next 7 days
    for day_offset in range(7):
        check_date = current + timedelta(days=day_offset)
        weekday = check_date.weekday()
        
        if weekday not in OPTIMAL_SCHEDULE:
            continue
        
        schedule = OPTIMAL_SCHEDULE[weekday]
        for idx, hour in enumerate(schedule["times"]):
            slot_time = check_date.replace(hour=hour, minute=0, second=0, microsecond=0)
            
            if slot_time > current:
                return {
                    "time": slot_time.strftime("%A %I:%M %p"),
                    "datetime": slot_time.isoformat(),
                    "content_type": schedule["content_types"][idx],
                    "priority": schedule["priority"][idx],
                    "day_name": slot_time.strftime("%A"),
                    "time_only": slot_time.strftime("%I:%M %p"),
                    "pillar": CONTENT_PILLARS.get(schedule["content_types"][idx], {})
                }
    
    return None

def generate_weekly_schedule():
    """Generate full week's posting schedule"""
    schedule = {}
    
    for weekday, config in OPTIMAL_SCHEDULE.items():
        day_name = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"][weekday]
        slots = []
        
        for idx, hour in enumerate(config["times"]):
            content_type = config["content_types"][idx]
            slots.append({
                "time": f"{hour:02d}:00",
                "content_type": content_type,
                "priority": config["priority"][idx],
                "pillar": CONTENT_PILLARS.get(content_type, {}),
                "keywords": CONTENT_PILLARS.get(content_type, {}).get("keywords", [])
            })
        
        schedule[day_name] = slots
    
    return schedule

def main():
    """Main scheduler logic"""
    # Check if ignore_schedule flag is set
    ignore_schedule = os.getenv("IGNORE_SCHEDULE", "false").lower() == "true"
    
    should_post, priority, content_type, current_time = should_post_now(ignore_schedule)
    next_slot = get_next_optimal_slot()
    weekly = generate_weekly_schedule()
    
    # Get pillar info for current content type
    current_pillar = CONTENT_PILLARS.get(content_type, {})
    
    # Create output
    output = {
        "metadata": {
            "scheduler_version": "2.0",
            "timezone": TIMEZONE,
            "niche": "motivation",
            "target_audience": "2AM scrollers, 5AM warriors, evening reflectors",
            "posting_philosophy": "Target emotional vulnerability moments"
        },
        "decision": {
            "should_post_now": should_post,
            "current_time": current_time.strftime("%Y-%m-%d %H:%M %Z"),
            "current_priority": priority,
            "current_content_type": content_type,
            "current_pillar": current_pillar,
            "reason": get_posting_reason(should_post, priority, content_type)
        },
        "schedule": {
            "next_optimal_slot": next_slot,
            "weekly_schedule": weekly
        },
        "content_pillars": CONTENT_PILLARS,
        "generated_at": datetime.now(pytz.UTC).isoformat()
    }
    
    # Save to file
    os.makedirs("tmp", exist_ok=True)
    with open("tmp/posting_schedule.json", "w") as f:
        json.dump(output, f, indent=2)
    
    # Print summary
    print_summary(should_post, current_time, priority, content_type, next_slot, weekly)
    
    # Set GitHub output
    if "GITHUB_OUTPUT" in os.environ:
        with open(os.environ["GITHUB_OUTPUT"], "a") as f:
            f.write(f"should_post={'true' if should_post else 'false'}\n")
            f.write(f"priority={priority}\n")
            f.write(f"content_type={content_type}\n")
            f.write(f"current_time={current_time.strftime('%Y-%m-%d %H:%M %Z')}\n")
            f.write(f"pillar_description={current_pillar.get('description', 'N/A')}\n")
            f.write(f"emotional_tone={current_pillar.get('emotional_tone', 'N/A')}\n")

def get_posting_reason(should_post, priority, content_type):
    """Get human-readable reason for posting decision"""
    if not should_post:
        return "Not within optimal posting window"
    if priority == "extreme":
        return "🔥 PRIME TIME - Highest virality window"
    elif priority == "highest":
        return "⭐ OPTIMAL - Peak engagement time"
    elif priority == "high":
        return "✅ Good time - Strong engagement expected"
    elif priority == "medium":
        return "💡 Acceptable time - Moderate engagement"
    else:
        return "⏳ Off-peak - Lower engagement expected"

def print_summary(should_post, current_time, priority, content_type, next_slot, weekly):
    """Print formatted summary"""
    print("\n" + "="*70)
    print("🔥 THE 5AM LEGION - POSTING SCHEDULER v2.0")
    print("="*70)
    print(f"Current Time: {current_time.strftime('%A, %B %d, %Y at %I:%M %p %Z')}")
    print(f"Should Post: {'✅ YES' if should_post else '❌ NO'}")
    print(f"Priority: {priority.upper()}")
    print(f"Content Type: {content_type.replace('_', ' ').title()}")
    print()
    
    if next_slot:
        print(f"📅 Next Optimal Slot:")
        print(f"   {next_slot['time']}")
        print(f"   Content: {next_slot['content_type'].replace('_', ' ').title()}")
        print(f"   Priority: {next_slot['priority'].upper()}")
        if next_slot.get('pillar'):
            print(f"   Description: {next_slot['pillar'].get('description', '')}")
    
    print()
    print("📊 This Week's Schedule:")
    for day, slots in weekly.items():
        print(f"\n{day}:")
        for slot in slots:
            emoji = "🔥" if slot['priority'] == "extreme" else "⭐" if slot['priority'] == "highest" else "✅" if slot['priority'] == "high" else "•"
            keywords = ", ".join(slot.get('keywords', [])[:2])
            print(f"  {emoji} {slot['time']} - {slot['content_type'].replace('_', ' ').title()}")
            print(f"       Priority: {slot['priority']} | Keywords: {keywords}")
    
    print("\n" + "="*70 + "\n")

if __name__ == "__main__":
    main()