"""Reminders that pop up (and can speak) at the right time.

Reminders are stored in SQLite, so they survive a restart. A small
background thread checks every few seconds and calls `on_due(reminder)`
for each reminder whose time has come.
"""

import re
import sqlite3
import threading
from datetime import datetime, timedelta

UNIT_SECONDS = {
    "second": 1, "seconds": 1, "sec": 1, "secs": 1, "sekunde": 1,
    "minute": 60, "minutes": 60, "min": 60, "mins": 60, "dakika": 60,
    "hour": 3600, "hours": 3600, "hr": 3600, "hrs": 3600, "saa": 3600,
}
UNITS = "|".join(sorted(UNIT_SECONDS, key=len, reverse=True))

# "remind me in 10 minutes to call mom" / "remind me to call mom in 10 minutes"
# "nikumbushe baada ya dakika 10 kupika" / "nikumbushe kupika baada ya dakika 10"
PATTERNS = [
    re.compile(rf"^remind me (?:in|after) (\d+) ({UNITS})\s*(?:to |that |about )?(.+)$"),
    re.compile(rf"^remind me (?:to |that |about )?(.+?) (?:in|after) (\d+) ({UNITS})$"),
    re.compile(rf"^nikumbushe baada ya ({UNITS}) (\d+),?\s*(?:kwamba |kuhusu )?(.+)$"),
    re.compile(rf"^nikumbushe (?:kwamba |kuhusu )?(.+?) baada ya ({UNITS}) (\d+)$"),
]
AT_PATTERNS = [
    re.compile(r"^remind me (?:at) (\d{1,2})[:.](\d{2})\s*(am|pm)?\s*(?:to |that |about )?(.+)$"),
    re.compile(r"^remind me (?:to |that |about )?(.+?) at (\d{1,2})[:.](\d{2})\s*(am|pm)?$"),
]


def parse_reminder(text):
    """Turn a sentence into (due_datetime, message), or None if it is not a reminder."""
    text = " ".join(text.lower().split()).strip(" .!?")
    now = datetime.now()

    for index, pattern in enumerate(PATTERNS):
        match = pattern.match(text)
        if not match:
            continue
        if index == 0:
            amount, unit, message = match.groups()
        elif index == 1:
            message, amount, unit = match.groups()
        elif index == 2:
            unit, amount, message = match.groups()
        else:
            message, unit, amount = match.groups()
        return now + timedelta(seconds=int(amount) * UNIT_SECONDS[unit]), message

    for index, pattern in enumerate(AT_PATTERNS):
        match = pattern.match(text)
        if not match:
            continue
        if index == 0:
            hour, minute, ampm, message = match.groups()
        else:
            message, hour, minute, ampm = match.groups()
        due = time_today(int(hour), int(minute), ampm)
        if due:
            return due, message
    return None


def time_today(hour, minute, ampm=None):
    """Next time the clock shows hour:minute (today, or tomorrow if passed)."""
    if ampm == "pm" and hour < 12:
        hour += 12
    if ampm == "am" and hour == 12:
        hour = 0
    if not (0 <= hour < 24 and 0 <= minute < 60):
        return None
    now = datetime.now()
    due = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if due <= now:
        due += timedelta(days=1)
    return due


class ReminderManager:
    def __init__(self, db_path, on_due=None, check_every=5):
        self.db_path = db_path
        self.on_due = on_due
        self.check_every = check_every
        self._stop = threading.Event()
        self._thread = None
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS reminders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    message TEXT NOT NULL,
                    due_at TEXT NOT NULL,
                    done INTEGER NOT NULL DEFAULT 0
                )
                """
            )

    def _connect(self):
        connection = sqlite3.connect(self.db_path, timeout=5)
        connection.row_factory = sqlite3.Row
        return connection

    def add(self, message, due_at):
        with self._connect() as connection:
            cursor = connection.execute(
                "INSERT INTO reminders (message, due_at) VALUES (?, ?)",
                (message.strip(), due_at.isoformat(timespec="seconds")),
            )
            return cursor.lastrowid

    def pending(self):
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT id, message, due_at FROM reminders WHERE done = 0 ORDER BY due_at"
            ).fetchall()
            return [dict(row) for row in rows]

    def cancel(self, reminder_id):
        with self._connect() as connection:
            cursor = connection.execute(
                "UPDATE reminders SET done = 1 WHERE id = ? AND done = 0", (reminder_id,)
            )
            return cursor.rowcount > 0

    # ------------------------------------------------------------------
    # Background checking
    # ------------------------------------------------------------------

    def start(self):
        if self._thread is None:
            self._thread = threading.Thread(target=self._loop, daemon=True)
            self._thread.start()

    def stop(self):
        self._stop.set()

    def _loop(self):
        while not self._stop.wait(self.check_every):
            try:
                self.check_now()
            except sqlite3.Error:
                pass  # try again on the next tick

    def check_now(self):
        now = datetime.now().isoformat(timespec="seconds")
        with self._connect() as connection:
            due = connection.execute(
                "SELECT id, message, due_at FROM reminders WHERE done = 0 AND due_at <= ?",
                (now,),
            ).fetchall()
            for row in due:
                connection.execute("UPDATE reminders SET done = 1 WHERE id = ?", (row["id"],))
        for row in due:
            if self.on_due:
                self.on_due(dict(row))
