#!/usr/bin/env python3
"""
🔥 Duration Validator - Pre-Upload Safety Check
Validates video meets 10-15 second target before upload

Features:
- Validates actual video duration
- Checks audio/video sync
- Verifies metadata files
- Configurable strict/warning mode
- Generates validation report
"""

import os
import json
import subprocess
import sys
from datetime import datetime

TMP = os.getenv("GITHUB_WORKSPACE", ".") + "/tmp"

# Duration targets (seconds)
TARGET_MIN = 9.0
TARGET_MAX = 16.0
OPTIMAL_MIN = 10.0
OPTIMAL_MAX = 15.0

# Validation mode
STRICT_MODE = os.getenv('STRICT_VALIDATION', 'false').lower() == 'true'


def get_video_duration(video_path):
    """Get actual video duration using ffprobe"""
    try:
        result = subprocess.run([
            'ffprobe',
            '-v', 'error',
            '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1',
            video_path
        ], capture_output=True, text=True, check=True)
        
        duration = float(result.stdout.strip())
        return duration
    except Exception as e:
        print(f"❌ Could not read video duration: {e}")
        return None


def get_audio_duration(audio_path):
    """Get audio duration using ffprobe"""
    try:
        result = subprocess.run([
            'ffprobe',
            '-v', 'error',
            '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1',
            audio_path
        ], capture_output=True, text=True, check=True)
        
        duration = float(result.stdout.strip())
        return duration
    except Exception as e:
        print(f"⚠️ Could not read audio duration: {e}")
        return None


def load_metadata_file(filepath, name):
    """Load and validate metadata JSON file"""
    if not os.path.exists(filepath):
        print(f"⚠️ {name} not found: {filepath}")
        return None
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print(f"✅ Loaded {name}")
        return data
    except Exception as e:
        print(f"⚠️ Could not load {name}: {e}")
        return None


def validate_video():
    """
    Main validation function
    
    Returns:
        (is_valid, validation_report)
    """
    
    print("\n" + "="*70)
    print("🔍 PRE-UPLOAD DURATION VALIDATION")
    print("="*70)
    print(f"Target range: {OPTIMAL_MIN}-{OPTIMAL_MAX}s (optimal)")
    print(f"Acceptable range: {TARGET_MIN}-{TARGET_MAX}s (acceptable)")
    print(f"Strict mode: {'ENABLED' if STRICT_MODE else 'DISABLED (warnings only)'}")
    print("")
    
    validation_report = {
        'validated_at': datetime.now().isoformat(),
        'target_min': TARGET_MIN,
        'target_max': TARGET_MAX,
        'optimal_min': OPTIMAL_MIN,
        'optimal_max': OPTIMAL_MAX,
        'strict_mode': STRICT_MODE,
        'checks': {},
        'warnings': [],
        'errors': [],
        'overall_status': 'UNKNOWN'
    }
    
    # Check 1: Video file exists
    print("📹 Checking video file...")
    video_path = os.path.join(TMP, "short.mp4")
    
    if not os.path.exists(video_path):
        error = f"Video file not found: {video_path}"
        print(f"❌ {error}")
        validation_report['errors'].append(error)
        validation_report['checks']['video_exists'] = False
        validation_report['overall_status'] = 'FAILED'
        return False, validation_report
    
    validation_report['checks']['video_exists'] = True
    print(f"✅ Video file exists: {video_path}")
    
    # Check 2: Get video duration
    print("\n⏱️ Checking video duration...")
    video_duration = get_video_duration(video_path)
    
    if video_duration is None:
        error = "Could not determine video duration"
        print(f"❌ {error}")
        validation_report['errors'].append(error)
        validation_report['checks']['duration_readable'] = False
        validation_report['overall_status'] = 'FAILED'
        return False, validation_report
    
    validation_report['checks']['duration_readable'] = True
    validation_report['video_duration'] = round(video_duration, 2)
    
    print(f"📊 Video duration: {video_duration:.2f}s")
    
    # Check 3: Validate duration against target
    print("\n🎯 Validating against target range...")
    
    within_optimal = OPTIMAL_MIN <= video_duration <= OPTIMAL_MAX
    within_acceptable = TARGET_MIN <= video_duration <= TARGET_MAX
    
    if within_optimal:
        print(f"✅ Duration {video_duration:.2f}s is OPTIMAL ({OPTIMAL_MIN}-{OPTIMAL_MAX}s)")
        validation_report['checks']['within_optimal'] = True
        validation_report['duration_status'] = 'OPTIMAL'
    elif within_acceptable:
        warning = f"Duration {video_duration:.2f}s is acceptable but not optimal (target: {OPTIMAL_MIN}-{OPTIMAL_MAX}s)"
        print(f"⚠️ {warning}")
        validation_report['warnings'].append(warning)
        validation_report['checks']['within_optimal'] = False
        validation_report['checks']['within_acceptable'] = True
        validation_report['duration_status'] = 'ACCEPTABLE'
    else:
        if video_duration > TARGET_MAX:
            error = f"Duration {video_duration:.2f}s EXCEEDS maximum {TARGET_MAX}s"
            severity = "❌ CRITICAL" if STRICT_MODE else "⚠️ WARNING"
            print(f"{severity}: {error}")
            print(f"   This will likely result in LOWER RETENTION RATES")
            validation_report['duration_status'] = 'TOO_LONG'
        else:
            error = f"Duration {video_duration:.2f}s BELOW minimum {TARGET_MIN}s"
            severity = "❌ CRITICAL" if STRICT_MODE else "⚠️ WARNING"
            print(f"{severity}: {error}")
            print(f"   Message may feel RUSHED")
            validation_report['duration_status'] = 'TOO_SHORT'
        
        if STRICT_MODE:
            validation_report['errors'].append(error)
            validation_report['checks']['within_acceptable'] = False
        else:
            validation_report['warnings'].append(error)
            validation_report['checks']['within_acceptable'] = False
    
    # Check 4: Audio sync
    print("\n🔊 Checking audio sync...")
    audio_path = os.path.join(TMP, "voice.mp3")
    
    if os.path.exists(audio_path):
        audio_duration = get_audio_duration(audio_path)
        
        if audio_duration:
            validation_report['audio_duration'] = round(audio_duration, 2)
            
            drift = abs(video_duration - audio_duration)
            drift_ms = drift * 1000
            
            print(f"   Audio: {audio_duration:.2f}s")
            print(f"   Video: {video_duration:.2f}s")
            print(f"   Drift: {drift_ms:.0f}ms")
            
            validation_report['drift_ms'] = round(drift_ms, 0)
            
            if drift < 0.05:
                print(f"   ✅ NEAR-PERFECT sync (<50ms)")
                validation_report['checks']['audio_sync'] = 'PERFECT'
            elif drift < 0.5:
                print(f"   ✅ Excellent sync (<500ms)")
                validation_report['checks']['audio_sync'] = 'EXCELLENT'
            else:
                warning = f"Audio/video drift {drift_ms:.0f}ms exceeds 500ms"
                print(f"   ⚠️ {warning}")
                validation_report['warnings'].append(warning)
                validation_report['checks']['audio_sync'] = 'ACCEPTABLE'
        else:
            validation_report['checks']['audio_sync'] = 'UNKNOWN'
    else:
        print(f"   ⚠️ Audio file not found (skipping sync check)")
        validation_report['checks']['audio_sync'] = 'SKIPPED'
    
    # Check 5: Metadata files
    print("\n📋 Checking metadata files...")
    
    script_data = load_metadata_file(
        os.path.join(TMP, "script.json"),
        "script.json"
    )
    
    audio_metadata = load_metadata_file(
        os.path.join(TMP, "audio_metadata.json"),
        "audio_metadata.json"
    )
    
    video_validation = load_metadata_file(
        os.path.join(TMP, "video_validation.json"),
        "video_validation.json"
    )
    
    validation_report['checks']['script_metadata_exists'] = script_data is not None
    validation_report['checks']['audio_metadata_exists'] = audio_metadata is not None
    validation_report['checks']['video_validation_exists'] = video_validation is not None
    
    # Check 6: Word count vs duration relationship
    if script_data:
        word_count = script_data.get('word_count', 0)
        estimated_duration = script_data.get('estimated_duration', 0)
        
        if word_count > 0:
            validation_report['word_count'] = word_count
            validation_report['estimated_duration'] = estimated_duration
            
            print(f"\n📝 Script Analysis:")
            print(f"   Word count: {word_count}")
            print(f"   Estimated duration: {estimated_duration:.2f}s")
            print(f"   Actual duration: {video_duration:.2f}s")
            
            estimation_error = abs(video_duration - estimated_duration)
            
            if estimation_error < 1.0:
                print(f"   ✅ Estimation accurate (error: {estimation_error:.2f}s)")
                validation_report['checks']['estimation_accuracy'] = 'GOOD'
            elif estimation_error < 2.0:
                print(f"   ⚠️ Estimation acceptable (error: {estimation_error:.2f}s)")
                validation_report['checks']['estimation_accuracy'] = 'ACCEPTABLE'
            else:
                warning = f"Estimation error {estimation_error:.2f}s exceeds 2s"
                print(f"   ⚠️ {warning}")
                validation_report['warnings'].append(warning)
                validation_report['checks']['estimation_accuracy'] = 'POOR'
    
    # Determine overall status
    print("\n" + "="*70)
    print("📊 VALIDATION SUMMARY")
    print("="*70)
    
    has_errors = len(validation_report['errors']) > 0
    has_warnings = len(validation_report['warnings']) > 0
    
    if has_errors:
        validation_report['overall_status'] = 'FAILED'
        print("❌ VALIDATION FAILED")
        print(f"\nErrors ({len(validation_report['errors'])}):")
        for error in validation_report['errors']:
            print(f"  ❌ {error}")
    elif has_warnings:
        validation_report['overall_status'] = 'WARNING'
        print("⚠️ VALIDATION PASSED WITH WARNINGS")
        print(f"\nWarnings ({len(validation_report['warnings'])}):")
        for warning in validation_report['warnings']:
            print(f"  ⚠️ {warning}")
    else:
        validation_report['overall_status'] = 'PASSED'
        print("✅ VALIDATION PASSED")
        print("   All checks passed successfully!")
    
    print("")
    print(f"Video Duration: {video_duration:.2f}s")
    print(f"Target Range: {OPTIMAL_MIN}-{OPTIMAL_MAX}s (optimal)")
    print(f"Status: {validation_report['duration_status']}")
    
    # Save validation report
    report_path = os.path.join(TMP, "duration_validation.json")
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(validation_report, f, indent=2)
    
    print(f"\n💾 Validation report saved: {report_path}")
    
    # Return result
    if STRICT_MODE and has_errors:
        print("\n❌ STRICT MODE: Blocking upload due to errors")
        return False, validation_report
    else:
        if has_warnings:
            print("\n⚠️ Proceeding with warnings (strict mode disabled)")
        return True, validation_report


def main():
    """Main entry point"""
    try:
        is_valid, report = validate_video()
        
        # Set GitHub Actions output
        if os.getenv('GITHUB_OUTPUT'):
            with open(os.getenv('GITHUB_OUTPUT'), 'a') as f:
                f.write(f"validation_status={report['overall_status']}\n")
                f.write(f"video_duration={report.get('video_duration', 0)}\n")
                f.write(f"within_target={'true' if report.get('checks', {}).get('within_acceptable', False) else 'false'}\n")
        
        # Exit based on validation result
        if STRICT_MODE and not is_valid:
            print("\n❌ Validation failed in strict mode - exiting with error")
            sys.exit(1)
        else:
            print("\n✅ Validation complete")
            sys.exit(0)
    
    except Exception as e:
        print(f"\n❌ VALIDATION ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()