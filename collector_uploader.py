# collector_uploader.py
import os
import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
from openai import OpenAI
from supabase import create_client
import json
import re

# -------------------
# Load environment variables
# -------------------
from dotenv import load_dotenv
load_dotenv()

OPENAI_ENDPOINT = os.getenv("OPENAI_ENDPOINT")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
DEPLOYMENT_NAME = "gpt-4o"

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# -------------------
# OpenAI Client
# -------------------
client = OpenAI(
    base_url=OPENAI_ENDPOINT,
    api_key=OPENAI_API_KEY
)

# -------------------
# Step 1: Scrape Ballon d'Or top players
# -------------------
URL = "https://www.goal.com/en-us/lists/ballon-dor-2025-official-rankings-ousmane-dembele-beats-lamine-yamal-vitinha/blta3aa18950f05b375"
response = requests.get(URL)
soup = BeautifulSoup(response.text, "html.parser")

players = []

# Find the script tag with __NEXT_DATA__ that contains the JSON data
next_data_script = soup.find("script", id="__NEXT_DATA__")
if next_data_script:
    try:
        next_data = json.loads(next_data_script.string)
        # Navigate to the slides data
        slides = next_data["props"]["pageProps"]["content"]["slideList"]["slides"]
        
        # Extract player data from slides
        for slide in slides:
            number = slide.get("number", "")
            headline = slide.get("headline", "")
            
            # The headline contains the player name and club
            if headline and number:
                # Extract player name and club from headline
                if "(" in headline and ")" in headline:
                    name = headline.split("(")[0].strip()
                    club = headline.split("(")[1].replace(")", "").strip()
                else:
                    name = headline.strip()
                    club = ""
                
                players.append({
                    "rank": int(number) if isinstance(number, (str, int)) and str(number).isdigit() else 0,
                    "name": name,
                    "club": club
                })
        
        # Sort by rank
        players.sort(key=lambda x: x["rank"])
        
    except (json.JSONDecodeError, KeyError) as e:
        print(f"Error parsing JSON data: {e}")
        players = []
else:
    print("Could not find __NEXT_DATA__ script tag")
    players = []

# Save raw blob
os.makedirs("data", exist_ok=True)
with open("data/raw_blob.txt", "w", encoding="utf-8") as f:
    f.write(json.dumps(players, indent=2))
    
print("=== DEBUG: Scraped players ===")
for p in players:
    print(f"{p['rank']}: {p['name']} ({p['club']})")

# -------------------
# Step 2: LLM Structuring to JSON
# -------------------
prompt = f"""
Convert the following list of soccer players into **strict JSON** only, with no explanations:
[
  {{
    "id": unique integer starting from 1,
    "ranking": integer,
    "name": string,
    "club": string,
    "source_url": "{URL}",
    "extracted_at": "YYYY-MM-DDTHH:MM:SS"
  }}
]
Here is the raw data:
{json.dumps(players)}
"""

llm_response = client.chat.completions.create(
    model=DEPLOYMENT_NAME,
    messages=[{"role": "user", "content": prompt}]
)

structured_json_text = llm_response.choices[0].message.content.strip()
print("\n=== DEBUG: Raw LLM output ===")
print(structured_json_text)

# Extract only the JSON array from the LLM output
match = re.search(r'\[.*\]', structured_json_text, re.DOTALL)
if match:
    structured_json_text = match.group(0)

print("\n=== DEBUG: Extracted JSON for parsing ===")
print(structured_json_text)

# Validate JSON
try:
    structured_data = json.loads(structured_json_text)
except json.JSONDecodeError:
    print("Failed to parse JSON from LLM output, using raw scraped data instead")
    # fallback: add unique IDs manually
    structured_data = []
    for idx, player in enumerate(players, start=1):
        structured_data.append({
            "id": idx,
            "ranking": player["rank"],
            "name": player["name"],
            "club": player["club"],
            "source_url": URL,
            "extracted_at": datetime.utcnow().isoformat()
        })

# -------------------
# Step 3: Upload to Supabase
# -------------------
if structured_data:
    df = pd.DataFrame(structured_data)
    df["updated_at"] = datetime.utcnow().isoformat()

    for row in df.to_dict(orient="records"):
        supabase.table("ballon_dor_players").upsert(row).execute()

print("Collector & uploader finished successfully! Uploaded players:")
for p in structured_data:
    print(f"{p['id']}: {p['ranking']} - {p['name']} ({p['club']})")
