from datetime import datetime, timedelta, date, timezone

utc_time = datetime.fromisoformat("2026-04-09T21:05:00+05:00")
print(utc_time.astimezone(tz=timezone.utc))