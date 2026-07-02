import copy
from datetime import timedelta
from pathlib import Path

import requests
import yaml
from icalendar import Alarm, Calendar


BASE_URL = "https://github.com/othyn/go-calendar/releases/latest/download/{}.ics"

AVAILABLE_CALENDARS = {
    "Community Day": "gocal__community_day",
    "Events": "gocal__event",
    "Raid Day": "gocal__raid_day",
    "Raid Hour": "gocal__raid_hour",
    "Raid Battles": "gocal__raid_battles",
    "Spotlight Hour": "gocal__pokemon_spotlight_hour",
    "GO Fest": "gocal__pokemon_go_fest",
    "GO Battle League": "gocal__go_battle_league",
    "GO Pass": "gocal__go_pass",
    "Max Mondays": "gocal__max_mondays",
    "Choose Your Path": "gocal__choose_your_path",
    "Season": "gocal__season",
}


def resolve_calendar_name(name):
    name = str(name).strip()

    if name in AVAILABLE_CALENDARS:
        return AVAILABLE_CALENDARS[name]

    if name in AVAILABLE_CALENDARS.values():
        return name

    available = "\n".join(f" - {key} -> {value}" for key, value in AVAILABLE_CALENDARS.items())
    raise ValueError(f"Calendrier inconnu : {name}\n\nCalendriers disponibles :\n{available}")


def parse_duration(value):
    value = str(value).strip().lower()
    number = int(value[:-1])
    unit = value[-1]

    if unit == "m":
        return timedelta(minutes=number)
    if unit == "h":
        return timedelta(hours=number)
    if unit == "d":
        return timedelta(days=number)

    raise ValueError(f"Durée invalide : {value}. Utilise m, h ou d.")


def make_alarm(duration):
    alarm = Alarm()
    alarm.add("action", "DISPLAY")
    alarm.add("description", "Rappel Pokémon GO")
    alarm.add("trigger", -parse_duration(duration))
    return alarm


config = yaml.safe_load(Path("config.yml").read_text(encoding="utf-8"))

selected_calendars = [
    resolve_calendar_name(name)
    for name in config.get("calendars", [])
]

exclude_terms = [
    term.lower()
    for term in config.get("exclude", [])
]

notifications = config.get("notifications", {})
default_alarms = notifications.get("default", [])
rules = notifications.get("rules", [])

output = Calendar()
output.add("prodid", "-//Personal Pokemon GO Calendar//FR")
output.add("version", "2.0")
output.add("x-wr-calname", "Pokémon GO - Favoris")
output.add("x-wr-timezone", "Europe/Paris")

for calendar_name in selected_calendars:
    url = BASE_URL.format(calendar_name)
    response = requests.get(url, timeout=30)
    response.raise_for_status()

    source_calendar = Calendar.from_ical(response.content)

    for component in source_calendar.walk():
        if component.name != "VEVENT":
            continue

        event = copy.deepcopy(component)
        title = str(event.get("summary", ""))

        if any(term in title.lower() for term in exclude_terms):
            continue

        event.subcomponents = [
            sub for sub in event.subcomponents
            if sub.name != "VALARM"
        ]

        alarms_to_add = default_alarms

        for rule in rules:
            match = str(rule.get("match", "")).lower()
            if match and match in title.lower():
                alarms_to_add = rule.get("alarms", [])
                break

        for alarm_duration in alarms_to_add:
            event.add_component(make_alarm(alarm_duration))

        output.add_component(event)

Path("public").mkdir(exist_ok=True)

with open("public/pokemon-go-favoris.ics", "wb") as f:
    f.write(output.to_ical())

with open("public/index.html", "w", encoding="utf-8") as f:
    f.write("""
<!doctype html>
<html>
<body>
<h1>Pokémon GO Calendar</h1>
<p><a href="pokemon-go-favoris.ics">pokemon-go-favoris.ics</a></p>
<p>Data powered by GO Calendar, ScrapedDuck and LeekDuck.com.</p>
</body>
</html>
""")
