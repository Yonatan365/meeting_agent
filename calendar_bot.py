"""
YAML meeting bot (scalar = free, mapping = booked).

pip install openai openai-agents-python pyyaml
export OPENAI_API_KEY=...
"""

import asyncio, os, datetime as dt, yaml
from typing import List, Dict, Union
from openai import OpenAI
import datetime
from agents import Agent, Runner, function_tool         # openai-agents-python ≥0.2
                                                       #  [oai_citation:8‡github.com](https://github.com/openai/openai-agents-python/issues/43?utm_source=chatgpt.com)
DB_PATH = "calendar.yml"
openai = OpenAI()
today = dt.date.today()            
weekday = today.strftime("%A")     
# ────────────────── persistence helpers ────────────────────────────
def _as_str_key(k):
    """Return k as ISO string if it's a date/datetime, else str(k)."""
    if isinstance(k, (datetime.date, datetime.datetime)):
        return k.isoformat()
    return str(k)

def load_db() -> dict[str, list]:
    """Load YAML and coerce *all* top-level keys to plain strings."""
    if not os.path.exists(DB_PATH):
        return {}
    data = yaml.safe_load(open(DB_PATH)) or {}
    return { _as_str_key(k): v for k, v in data.items() }

def save_db(db: dict[str, list]) -> None:
    """Dump after key-normalisation so we never re-introduce date keys."""
    clean = { _as_str_key(k): v for k, v in db.items() }
    yaml.safe_dump(clean, open(DB_PATH, "w"), sort_keys=False)

# ───────────────────── list helper ─────────────────────────────────
def split_day(day: List[Union[str, Dict[str, str]]]):
    """Return (free:list[str], booked:list[dict]) from mixed list."""
    free, booked = [], []
    for item in day:
        if isinstance(item, str):
            free.append(item)
        elif isinstance(item, dict):
            # one-key mapping: {"10:00": "name"}
            hour, name = next(iter(item.items()))
            booked.append({"hour": hour, "attendee": name})
    return free, booked

# ───────────────────── agent tools ────────────────────────────────
@function_tool
def list_slots(date_iso: str | None = None) -> Dict[str, List]:
    """
    Return {'free': [...], 'booked': [{'hour':str,'attendee':str}, ...]}.
    Defaults to tomorrow (UTC) if date omitted.
    """
    date = date_iso or (dt.date.today() + dt.timedelta(days=1)).isoformat()
    free, booked = split_day(load_db().get(date, []))
    return {"free": free, "booked": booked}

@function_tool
def book_slot(date_iso: str, hour: str, attendee: str) -> str:
    """
    Book *hour* on *date_iso* for *attendee* (must be free).
    """
    db = load_db()
    day = db.setdefault(date_iso, [])
    # 1. ensure hour is free
    if hour not in [s for s in day if isinstance(s, str)]:
        raise ValueError("Slot unavailable")
    # 2. replace scalar with mapping
    day[day.index(hour)] = {hour: attendee}
    save_db(db)
    return f"Booked {hour} on {date_iso} for {attendee}"

@function_tool
def cancel_slot(date_iso: str, hour: str | None = None, attendee: str | None = None) -> str:
    """
    Cancel a booking.  If *hour* is None the tool will:
      • look up all bookings matching *attendee* on *date_iso*
      • if exactly one match → cancel it
      • otherwise raise ValueError so the model knows to ask.
    """
    db = load_db()
    day = db.get(date_iso, [])
    # helper to flatten bookings
    matches = [item for item in day if isinstance(item, dict)
               and (hour is None or hour in item)
               and (attendee is None or attendee.lower() == list(item.values())[0].lower())]

    if len(matches) != 1:
        raise ValueError("AMBIGUOUS")        # tells LLM to ask user
    item = matches[0]
    hour = next(iter(item))
    day.remove(item)
    day.append(hour)                         # free again
    save_db(db)
    return f"Cancelled {hour} on {date_iso}"

# ──────────────────── agent definition ────────────────────────────
scheduler = Agent(
    name="YAML-Calendar-Bot",
    instructions=f"""
You are **Yonatan’s customer-facing scheduling assistant**.
Your only job is to chat with clients, offer free slots, and book or
cancel meetings on Yonatan’s behalf through the tools.

Current date: {weekday}, {today.isoformat()}.

## Tools
• list_slots(date_iso) → returns {{ "free": [HH:MM, …], "booked": […] }}  
• book_slot(date_iso, hour, attendee)  
• cancel_slot(date_iso, hour \| null, attendee) …

## Operating rules
1. **Booking** – always ask for or confirm the attendee’s name before
   calling *book_slot* and confirm afterwards in plain language.
2. **Cancellation** – if the user gives a name but no time, look up their
   bookings that day; if exactly one exists, call
   *cancel_slot(date_iso, null, name)*, then confirm. Otherwise ask which
   time. …
3. Never reveal booked slots—only free ones.
4. Keep replies concise, friendly, decisive; times are 24-hour, 1-hour
   blocks.
""",
    model="o3-mini",
    tools=[list_slots, book_slot, cancel_slot],
)

async def main() -> None:
    tomorrow = (dt.date.today() + dt.timedelta(days=1)).isoformat()

    # 1st turn ---------------------------------------------------------
    result1 = await Runner.run(
        scheduler,
        f"What time slots are free on {tomorrow}?"
    )
    print(result1.final_output)

    # 2nd turn ---------------------------------------------------------
    convo = result1.to_input_list() + [  # keep all prior messages
        {"role": "user", "content": f"Book {tomorrow} 10:00 for Yonatan."}
    ]
    result2 = await Runner.run(scheduler, convo)
    print(result2.final_output)

    # 3rd turn ---------------------------------------------------------
    convo = result2.to_input_list() + [
        {"role": "user", "content": f"Cancel Yonatan's 10:00 on {tomorrow}."}
    ]
    result3 = await Runner.run(scheduler, convo)
    print(result3.final_output)

if __name__ == "__main__":
    asyncio.run(main())