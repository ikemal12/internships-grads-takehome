# On-Call Schedule Renderer

A Python script that generates on-call schedules with support for overrides.

## Requirements

- Python 3.7 or higher (no external dependencies)

## Usage

Run the script with schedule configuration, overrides, and time range:

```bash
./render-schedule \
    --schedule=schedule.json \
    --overrides=overrides.json \
    --from='2025-11-07T17:00:00Z' \
    --until='2025-11-21T17:00:00Z'
```

Or directly with Python:

```bash
python render-schedule.py \
    --schedule=schedule.json \
    --overrides=overrides.json \
    --from='2025-11-07T17:00:00Z' \
    --until='2025-11-21T17:00:00Z'
```

### Input Format

**schedule.json** - Schedule configuration:
```json
{
  "users": ["alice", "bob", "charlie"],
  "handover_start_at": "2025-11-07T17:00:00Z",
  "handover_interval_days": 7
}
```

**overrides.json** - Array of temporary shift overrides:
```json
[
  {
    "user": "charlie",
    "start_at": "2025-11-10T17:00:00Z",
    "end_at": "2025-11-10T22:00:00Z"
  }
]
```

### Output

JSON array of schedule entries with overrides applied:
```json
[
  {
    "user": "alice",
    "start_at": "2025-11-07T17:00:00Z",
    "end_at": "2025-11-10T17:00:00Z"
  },
  {
    "user": "charlie",
    "start_at": "2025-11-10T17:00:00Z",
    "end_at": "2025-11-10T22:00:00Z"
  }
]
```
