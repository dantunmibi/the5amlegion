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
TIMEZONE = os.getenv("SCHEDULER_TIMEZONE", "US/Eastern")  # EST/EDT by default

# Motivation content performs best at these times:
OPTIMAL_SCHEDULE = {
    # Every day (Monday=0 to Sunday=6) focuses on the same two powerful slots.
    # Slot 1: 7 AM EST (Morning Ignition) - Catches the entire US wake-up window.
    # Slot 2: 10 PM EST (Nightly Reckoning) - Catches the evening/late-night scroll.
    0: {"times": [7, 22], "content_types": ["morning_fire", "late_night_accountability"], "priority": ["highest", "extreme"]},
    1: {"times": [7, 22], "content_types": ["morning_fire", "late_night_accountability"], "priority": ["highest", "extreme"]},
    2: {"times": [7, 22], "content_types": ["morning_fire", "late_night_accountability"], "priority": ["highest", "extreme"]},
    3: {"times": [7, 22], "content_types": ["morning_fire", "late_night_accountability"], "priority": ["highest", "extreme"]},
    4: {"times": [7, 22], "content_types": ["morning_fire", "late_night_accountability"], "priority": ["highest", "extreme"]},
    # Weekends use specific pillars but at the same high-impact times.
    5: {"times": [7, 22], "content_types": ["weekend_grind", "reflection"], "priority": ["highest", "extreme"]},
    6: {"times": [7, 22], "content_types": ["sunday_motivation", "week_prep"], "priority": ["highest", "extreme"]},
}

# Content pillar mapping
CONTENT_PILLARS = {
    # Morning Ignition Pillars (for the 7 AM slot)
    "morning_fire": {
        "description": "Direct, aggressive wake-up call to conquer the day.",
        "emotional_tone": "intense_commanding",
        "keywords": ["wakeup", "5amclub", "noexcuses", "warrior", "conquer"]
    },
    "sunday_motivation": {
        "description": "The week is a battle. Today is when you sharpen your sword.",
        "emotional_tone": "hopeful_determined",
        "keywords": ["weekahead", "prepare", "sundayreset", "vision", "dominate"]
    },
    "weekend_grind": {
        "description": "They are resting. You are working. This is the gap.",
        "emotional_tone": "defiant_energetic",
        "keywords": ["noweakends", "outwork", "saturdaygrind", "consistency", "nooffdays"]
    },
    # Nightly Reckoning Pillars (for the 10 PM slot)
    "late_night_accountability": {
        "description": "The day is over. Look in the mirror. Were you a warrior or a coward? Be honest.",
        "emotional_tone": "intimate_confrontational",
        "keywords": ["accountability", "truth", "bereal", "no_lies", "reflection"]
    },
    "reflection": {
        "description": "The week is done. Are you proud of the effort? That honesty fuels next week.",
        "emotional_tone": "sober_honest",
        "keywords": ["reflect", "honest", "review", "learn", "prepare"]
    },
    "week_prep": {
        "description": "Your rivals are sleeping. You are planning victory. The week is won tonight.",
        "emotional_tone": "scheming_confident",
        "keywords": ["weekprep", "strategy", "goals", "ambition", "monday"]
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