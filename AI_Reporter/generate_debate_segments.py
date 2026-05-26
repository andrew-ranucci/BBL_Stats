import os
import json
import re

source_folder = r"C:\Users\andre\BBL_Stats\AI_Reporter\Debate_Segments"

# This is the path the website will use.
# Make sure the Debate_Segments folder is inside your website project.
website_audio_path = "./AI_Reporter/Debate_Segments"

output_file = "data/debate_segments.json"

pattern = re.compile(r"^debate_(.+)_week(\d+)\.wav$", re.IGNORECASE)

segments = []

for filename in os.listdir(source_folder):
    match = pattern.match(filename)

    if not match:
        continue

    player_name = match.group(1).replace("_", " ").replace("-", " ").strip()
    week = int(match.group(2))

    segments.append({
        "label": f"Week {week} - {player_name}",
        "player": player_name,
        "week": week,
        "file": f"{website_audio_path}/{filename}"
    })

segments.sort(key=lambda x: (x["week"], x["player"]))

os.makedirs("data", exist_ok=True)

with open(output_file, "w", encoding="utf-8") as f:
    json.dump(segments, f, indent=2)

print(f"Saved {len(segments)} debate segments to {output_file}")