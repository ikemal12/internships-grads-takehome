import argparse
import json
from datetime import datetime, timezone
from typing import List, Dict, Any


def parse_datetime(dt_str: str) -> datetime:
    """Parse ISO 8601 datetime string to datetime object."""
    return datetime.fromisoformat(dt_str.replace('Z', '+00:00'))


def generate_base_schedule(schedule: Dict[str, Any], from_dt: datetime, until_dt: datetime) -> List[Dict[str, Any]]:
    """Generate the base schedule entries without overrides."""
    users = schedule['users']
    handover_start = parse_datetime(schedule['handover_start_at'])
    interval_days = schedule['handover_interval_days']
    
    entries = []
    user_index = 0
    current_start = handover_start
    
    # Find the first relevant shift (could be before 'from' if we need to find active shift)
    while current_start < from_dt:
        next_start = datetime.fromtimestamp(
            current_start.timestamp() + interval_days * 86400,
            tz=timezone.utc
        )
        if next_start > from_dt:
            break
        current_start = next_start
        user_index = (user_index + 1) % len(users)
    
    # Generate entries within the range
    while current_start < until_dt:
        next_start = datetime.fromtimestamp(
            current_start.timestamp() + interval_days * 86400,
            tz=timezone.utc
        )
        
        entry_start = max(current_start, from_dt)
        entry_end = min(next_start, until_dt)
        
        if entry_start < entry_end:
            entries.append({
                'user': users[user_index],
                'start_at': entry_start.isoformat().replace('+00:00', 'Z'),
                'end_at': entry_end.isoformat().replace('+00:00', 'Z')
            })
        
        current_start = next_start
        user_index = (user_index + 1) % len(users)
    
    return entries


def apply_overrides(base_entries: List[Dict[str, Any]], overrides: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Apply overrides to base schedule entries, splitting and replacing as needed."""
    # Convert all timestamps to datetime objects for easier comparison
    timeline = []
    for entry in base_entries:
        timeline.append({
            'user': entry['user'],
            'start': parse_datetime(entry['start_at']),
            'end': parse_datetime(entry['end_at']),
            'is_override': False
        })
    
    for override in overrides:
        timeline.append({
            'user': override['user'],
            'start': parse_datetime(override['start_at']),
            'end': parse_datetime(override['end_at']),
            'is_override': True
        })
    
    # Process timeline: split base entries where overrides intersect
    result = []
    base_segments = [seg for seg in timeline if not seg['is_override']]
    override_segments = [seg for seg in timeline if seg['is_override']]
    
    for base in base_segments:
        segments = [(base['start'], base['end'], base['user'])]
        
        # Apply each override to the current segments
        for override in override_segments:
            new_segments = []
            for start, end, user in segments:
                # No overlap
                if override['end'] <= start or override['start'] >= end:
                    new_segments.append((start, end, user))
                # Override completely covers segment
                elif override['start'] <= start and override['end'] >= end:
                    new_segments.append((start, end, override['user']))
                # Override at the start
                elif override['start'] <= start and override['end'] < end:
                    new_segments.append((start, override['end'], override['user']))
                    new_segments.append((override['end'], end, user))
                # Override at the end
                elif override['start'] > start and override['end'] >= end:
                    new_segments.append((start, override['start'], user))
                    new_segments.append((override['start'], end, override['user']))
                # Override in the middle
                else:
                    new_segments.append((start, override['start'], user))
                    new_segments.append((override['start'], override['end'], override['user']))
                    new_segments.append((override['end'], end, user))
            
            segments = new_segments
        
        result.extend(segments)
    
    # Sort by start time and merge consecutive segments with the same user
    result.sort(key=lambda x: x[0])
    
    merged = []
    for start, end, user in result:
        if merged and merged[-1][2] == user and merged[-1][1] == start:
            merged[-1] = (merged[-1][0], end, user)
        else:
            merged.append((start, end, user))
    
    # Convert back to the output format
    return [
        {
            'user': user,
            'start_at': start.isoformat().replace('+00:00', 'Z'),
            'end_at': end.isoformat().replace('+00:00', 'Z')
        }
        for start, end, user in merged
    ]


def main():
    parser = argparse.ArgumentParser(description='Render on-call schedule with overrides')
    parser.add_argument('--schedule', required=True, help='Path to schedule JSON file')
    parser.add_argument('--overrides', required=True, help='Path to overrides JSON file')
    parser.add_argument('--from', dest='from_time', required=True, help='Start time (ISO 8601)')
    parser.add_argument('--until', required=True, help='End time (ISO 8601)')
    
    args = parser.parse_args()
    
    with open(args.schedule, 'r') as f:
        schedule = json.load(f)
    
    with open(args.overrides, 'r') as f:
        overrides = json.load(f)
    
    from_dt = parse_datetime(args.from_time)
    until_dt = parse_datetime(args.until)
    
    base_entries = generate_base_schedule(schedule, from_dt, until_dt)
    final_entries = apply_overrides(base_entries, overrides)
    
    print(json.dumps(final_entries, indent=2))


if __name__ == '__main__':
    main()
