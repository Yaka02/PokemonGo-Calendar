import requests
from icalendar import Calendar
from pathlib import Path

CALENDARS = [
    "community_day",
    "event",
    "raid_day",
    "pokemon_go_fest",
]

BASE_URL = "https://github.com/othyn/go-calendar/releases/latest/download/{}.ics"

output = Calendar()
output.add("prodid", "-//Personal Pokemon GO Calendar//FR")
output.add("version", "2.0")
output.add("x-wr-calname", "Pokémon GO - Favoris")
output.add("x-wr-timezone", "Europe/Paris")

for name in CALENDARS:
    url = BASE_URL.format(name)
    response = requests.get(url, timeout=30)
    response.raise_for_status()

    calendar = Calendar.from_ical(response.content)

    for component in calendar.walk():
        if component.name == "VEVENT":
            output.add_component(component)

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
