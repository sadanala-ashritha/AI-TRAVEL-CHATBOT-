from flask import Flask, render_template, request
import wikipedia
import urllib.parse
import requests
import threading
import webbrowser

# === Flask App Initialization ===
app = Flask(__name__)

# === OpenRouter API Setup ===
API_KEY = "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"
HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
    "HTTP-Referer": "http://localhost:5000",
    "X-Title": "GuideYourTrip"
}

# === Utility Functions ===
def get_maps_link(place, city=""):
    query = f"{place}, {city}" if city else place
    return f"https://www.google.com/maps/search/{urllib.parse.quote(query)}"

def get_city_description(city):
    try:
        return wikipedia.summary(city, sentences=3, auto_suggest=False)
    except:
        return f"{city.title()} is a beautiful place known for its culture and attractions."

def fetch_wiki_summary(place):
    try:
        return wikipedia.summary(place, sentences=1, auto_suggest=False)
    except:
        return "No summary available."

def get_travel_info(city):
    url = "https://openrouter.ai/api/v1/chat/completions"
    prompt = f"""You are a travel assistant. Provide information about {city} in the following strict format:

Places:
- Place1
- Place2

Foods:
- Food1
- Food2

Malls:
- Mall1
- Mall2

Restaurants:
- Restaurant1
- Restaurant2"""

    data = {
        "model": "openai/gpt-3.5-turbo",  # safer model, change if LLaMA is confirmed to be working
        "messages": [
            {"role": "system", "content": "You are a travel assistant."},
            {"role": "user", "content": prompt}
        ]
    }

    response = requests.post(url, headers=HEADERS, json=data)
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]

def parse_travel_info(raw_text):
    sections = {"places": [], "foods": [], "malls": [], "restaurants": []}
    current = None
    for line in raw_text.splitlines():
        line = line.strip()
        if not line:
            continue
        if line.lower().startswith("places:"):
            current = "places"
        elif line.lower().startswith("foods:"):
            current = "foods"
        elif line.lower().startswith("malls:"):
            current = "malls"
        elif line.lower().startswith("restaurants:"):
            current = "restaurants"
        elif current and line.startswith("-"):
            sections[current].append(line[1:].strip())
    return sections

def generate_itinerary(city, days):
    url = "https://openrouter.ai/api/v1/chat/completions"
    prompt = (
        f"Create a {days}-day travel itinerary for {city}.\n"
        "For each day, include:\n"
        "- One tourist attraction to visit (with a 1-line description)\n"
        "- One food place to visit (restaurant, street food stall, etc.)\n"
        "- One must-try local food item\n"
        "Format:\n\n"
        "Day 1:\n"
        "Place: [Place Name] - [Short Description]\n"
        "Food Place: [Food Place Name]\n"
        "Must-Try Food: [Food Item]"
    )

    data = {
        "model": "openai/gpt-3.5-turbo",
        "messages": [
            {"role": "system", "content": "You are an itinerary planner."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
        "max_tokens": 1000
    }

    response = requests.post(url, headers=HEADERS, json=data)
    response.raise_for_status()
    content = response.json()["choices"][0]["message"]["content"]

    itinerary = {}
    current_day = None

    for line in content.splitlines():
        line = line.strip()
        if line.lower().startswith("day"):
            current_day = line.rstrip(":")
            itinerary[current_day] = []
        elif line.lower().startswith("place:"):
            place_line = line[len("Place:"):].strip()
            if " - " in place_line:
                place, description = place_line.split(" - ", 1)
            else:
                place, description = place_line, "No description available."
        elif line.lower().startswith("food place:"):
            food_place = line[len("Food Place:"):].strip()
        elif line.lower().startswith("must-try food:"):
            must_try_food = line[len("Must-Try Food:"):].strip()
            if current_day and place and food_place and must_try_food:
                summary = fetch_wiki_summary(place)
                map_link = get_maps_link(place, city)
                itinerary[current_day].append({
                    "place": place,
                    "description": description,
                    "summary": summary,
                    "map": map_link,
                    "food_place": food_place,
                    "food_item": must_try_food
                })

    return itinerary

# === Routes ===

@app.route("/")
def welcome_page():
    return render_template("welcome_page.html")

@app.route("/index", methods=["GET", "POST"])
def index():
    result = {}
    city = request.form.get("city", "").strip() if request.method == "POST" else ""

    if city:
        description = get_city_description(city)
        travel_info = get_travel_info(city)
        parsed_info = parse_travel_info(travel_info)
        result = {
            "city": city.title(),
            "description": description,
            "maps_link": get_maps_link(city),
            "sections": parsed_info
        }
    return render_template("index.html", result=result, get_maps_link=get_maps_link)

@app.route("/itinerary", methods=["GET", "POST"])
def itinerary_page():
    if request.method == "POST":
        city = request.form['city']
        days = int(request.form['days'])
        itinerary = generate_itinerary(city, days)
        return render_template("itinerary_result.html", city=city, days=days, itinerary=itinerary)
    return render_template("itinerary_form.html")

# === Launch Browser ===
def open_browser():
    webbrowser.open_new("http://127.0.0.1:5000")

if __name__ == "__main__":
    threading.Timer(1.0, open_browser).start()
    app.run(debug=True, use_reloader=False)
