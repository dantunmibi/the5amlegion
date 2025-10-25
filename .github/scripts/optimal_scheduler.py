#!/usr/bin/env python3
"""
🔥 THE 5AM LEGION - Optimal Posting Scheduler
Targets 2AM scrollers, 5AM warriors, and evening reflectors
"""

import os
import json
from datetime import datetime, timedelta
import pytz

# Motivation content performs best at these times (EST):
OPTIMAL_SCHEDULE = {
    # Monday: Start strong
    0: {
        "times": [5, 20],  # 5 AM (morning fire), 8 PM (reflection)
        "content_types": ["morning_fire", "evening_reflection"],
        "priority": ["highest", "high"]
    },
    # Tuesday: Triple threat
    1: {
        "times": [6, 12, 23],  # 6 AM, 12 PM, 11 PM
        "content_types": ["discipline", "midday_boost", "late_night_accountability"],
        "priority": ["highest", "medium", "extreme"]  # Late night is PRIME
    },
    # Wednesday: Mid-week motivation
    2: {
        "times": [5, 19],  # 5 AM, 7 PM
        "content_types": ["morning_fire", "mindset_shift"],
        "priority": ["highest", "high"]
    },
    # Thursday: Include 2AM slot (VIRAL TIME)
    3: {
        "times": [2, 6],  # 2 AM (crisis time), 6 AM
        "content_types": ["late_night_truth", "discipline"],
        "priority": ["extreme", "highest"]  # 2 AM is GOLD
    },
    # Friday: Weekend prep
    4: {
        "times": [5, 18],  # 5 AM, 6 PM
        "content_types": ["morning_fire", "weekend_prep"],
        "priority": ["highest", "high"]
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
        "priority": ["highest", "high", "high", "extreme"]  # Sunday 1 AM is VIRAL
    }
}

# Content pillar mapping
CONTENT_PILLARS = {
    "morning_fire": {
        "percentage": 30,
        "description": "Aggressive wake-up calls, 5AM warrior content",
        "emotional_tone": "intense",
        "visual_style": "sunrise, training, warrior"
    },
    "discipline": {
        "percentage": 25,
        "description": "Hard work, no excuses, relentless grind",
        "emotional_tone": "commanding",
        "visual_style": "training montages, struggle, victory"
    },
    "mindset_shift": {
        "percentage": 20,
        "description": "Reframe failure, change beliefs, mental toughness",
        "emotional_tone": "contemplative_powerful",
        "visual_style": "reflective, journey, transformation"
    },
    "late_night_accountability": {
        "percentage": 15,
        "description": "2AM scrollers, existential crisis, late night truth",
        "emotional_tone": "intimate_honest",
        "visual_style": "dark, alone, city at night"
    },
    "success_stories": {
        "percentage": 10,
        "description": "Transformation proof, it's possible, inspiration",
        "emotional_tone": "aspirational",
        "visual_style": "before/after, celebration, achievement"
    }
}

def get_current_time():
    """Get current time in EST"""
    est = pytz.timezone('US/Eastern')
    return datetime.now(est)

def should_post_now():
    """Determine if current time is optimal for posting"""
    current = get_current_time()
    weekday = current.weekday()
    hour = current.hour
    
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
                    "time": slot_time.strftime("%A %I:%M %p EST"),
                    "datetime": slot_time.isoformat(),
                    "content_type": schedule["content_types"][idx],
                    "priority": schedule["priority"][idx],
                    "day_name": slot_time.strftime("%A"),
                    "time_only": slot_time.strftime("%I:%M %p")
                }
    
    return None

def generate_weekly_schedule():
    """Generate full week's posting schedule"""
    schedule = {}
    
    for weekday, config in OPTIMAL_SCHEDULE.items():
        day_name = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"][weekday]
        slots = []
        
        for idx, hour in enumerate(config["times"]):
            slots.append({
                "time": f"{hour:02d}:00",
                "content_type": config["content_types"][idx],
                "priority": config["priority"][idx],
                "pillar": config["content_types"][idx]
            })
        
        schedule[day_name] = slots
    
    return schedule

def main():
    """Main scheduler logic"""
    should_post, priority, content_type, current_time = should_post_now()
    next_slot = get_next_optimal_slot()
    weekly = generate_weekly_schedule()
    
    # Create output
    output = {
        "should_post_now": should_post,
        "current_time": current_time.strftime("%Y-%m-%d %H:%M EST"),
        "current_priority": priority,
        "current_content_type": content_type,
        "next_optimal_slot": next_slot,
        "weekly_schedule": weekly,
        "content_pillars": CONTENT_PILLARS,
        "niche": "motivation",
        "target_audience": "2AM scrollers, 5AM warriors, evening reflectors",
        "posting_philosophy": "Target emotional vulnerability moments"
    }
    
    # Save to file
    os.makedirs("tmp", exist_ok=True)
    with open("tmp/posting_schedule.json", "w") as f:
        json.dump(output, f, indent=2)
    
    # Print summary
    print("=" * 60)
    print("🔥 THE 5AM LEGION - POSTING SCHEDULER")
    print("=" * 60)
    print(f"Current Time: {current_time.strftime('%A, %B %d, %Y at %I:%M %p EST')}")
    print(f"Should Post: {'✅ YES' if should_post else '❌ NO'}")
    print(f"Priority: {priority.upper()}")
    print(f"Content Type: {content_type.replace('_', ' ').title()}")
    print()
    
    if next_slot:
        print(f"📅 Next Optimal Slot:")
        print(f"   {next_slot['time']}")
        print(f"   Content: {next_slot['content_type'].replace('_', ' ').title()}")
        print(f"   Priority: {next_slot['priority'].upper()}")
    
    print()
    print("📊 This Week's Schedule:")
    for day, slots in weekly.items():
        print(f"\n{day}:")
        for slot in slots:
            emoji = "🔥" if slot['priority'] == "extreme" else "⭐" if slot['priority'] == "highest" else "•"
            print(f"  {emoji} {slot['time']} - {slot['content_type'].replace('_', ' ').title()} ({slot['priority']})")
    
    print("\n" + "=" * 60)
    
    # Set GitHub output
    if "GITHUB_OUTPUT" in os.environ:
        with open(os.environ["GITHUB_OUTPUT"], "a") as f:
            f.write(f"should_post={'true' if should_post else 'false'}\n")
            f.write(f"priority={priority}\n")
            f.write(f"content_type={content_type}\n")
            f.write(f"current_time={current_time.strftime('%Y-%m-%d %H:%M EST')}\n")

if __name__ == "__main__":
    main()