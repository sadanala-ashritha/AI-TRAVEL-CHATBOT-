from flask import Flask, render_template, request
import wikipedia
import openai 
import urllib.parse


openai.api_base = "https://openrouter.ai/api/v1"
openai.api_key = "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"

# Required for OpenRouter
openai.default_headers = {
    "Authorization": "Bearer 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"
}




def get_maps_link(place, city):
    query = urllib.parse.quote(f"{place} {city}")
    return f"https://www.google.com/maps/search/?api=1&query={query}"

def get_city_description(city):
    try:
        summary = wikipedia.summary(city, sentences=3, auto_suggest=False)
        return summary
    except wikipedia.DisambiguationError as e:
        try:
            summary = wikipedia.summary(e.options[0], sentences=3, auto_suggest=False)
            return summary
        except:
            return "❗ Couldn't find a proper description for this city."
    except:
        return "❗ Couldn't find a proper description for this city."
    
def get_travel_info(city):
    prompt = f"""You are a travel assistant. Provide information about {city} in the following strict format. Do not include any other text, comments, or headings.

    Places:
    - Place1
    - Place2
    - Place3

    Foods:
    - Food1
    - Food2
    - Food3

    Malls:
    - Mall1
    - Mall2
    - Mall3

    Restaurants:
    - Restaurant1
    - Restaurant2
    - Restaurant3

    Only use this format. Do NOT include section labels like 'Travel details' or 'Popular places'. No introductory text. Just start directly with 'Places:'."""


    

    response = openai.ChatCompletion.create(
        model="meta-llama/llama-3.3-8b-instruct:free",  # or "gpt-4" if your key supports it
        messages=[
            {"role": "system", "content": "You are a travel assistant."},
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content
    
app = Flask(__name__)

def get_city_description(city):
    try:
        summary = wikipedia.summary(city, sentences=3, auto_suggest=False)
        return summary
    except:
        return f"{city.title()} is a beautiful place known for its culture and attractions."
def get_maps_link(place, city=""):
    query = f"{place}, {city}" if city else place
    return f"https://www.google.com/maps/search/{urllib.parse.quote(query)}"

@app.route("/")
def welcome_page():
    return render_template("welcome_page.html")

@app.route("/index", methods=["GET", "POST"])
def index():
    city = request.form.get("city", "").strip()
    result = {}

    if request.method == "POST" and city:
        description = get_city_description(city)
        maps_link = get_maps_link(city)

        def parse_travel_info(raw_text):
            sections = {
                "places": [],
                "foods": [],
                "malls": [],
                "restaurants": []
            }

            current_section = None
            for line in raw_text.split('\n'):
                line = line.strip()
                if not line:
                    continue

                # Detect section headers
                if line.lower().startswith("places:"):
                    current_section = "places"
                elif line.lower().startswith("foods:"):
                    current_section = "foods"
                elif line.lower().startswith("malls:"):
                    current_section = "malls"
                elif line.lower().startswith("restaurants:"):
                    current_section = "restaurants"
                elif current_section and line.startswith(("-", "•")):
                    # Add cleaned item to current section
                    cleaned = line.lstrip("-• ").strip()
                    if cleaned:
                        sections[current_section].append(cleaned)

            return sections
        raw_info = get_travel_info(city)
        section_data = parse_travel_info(raw_info)
        print("RAW INFO:", raw_info)
        print("PARSED DATA:", section_data)

        result = {
            "city": city.title(),
            "description": description,
            "maps_link": maps_link,
            "sections": section_data,
        }

    return render_template("index.html", result=result, get_maps_link=get_maps_link)


import webbrowser
import threading

def open_browser():
    webbrowser.open_new("http://127.0.0.1:5000")

if __name__ == "__main__":
    threading.Timer(1.0, open_browser).start()  # Open after 1 second
    app.run(debug=True, use_reloader=False)



    
