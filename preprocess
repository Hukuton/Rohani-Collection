import json
import os
import re
import time

print("Starting Data Pre-Processing...")

RAW_FILE = 'hymns.json'
CLEAN_DIR = 'cleaned'
CLEAN_FILE = os.path.join(CLEAN_DIR, 'hymn.json')
VERSION_FILE = os.path.join(CLEAN_DIR, 'version.json')

# Create the "cleaned" directory if it doesn't exist
if not os.path.exists(CLEAN_DIR):
    os.makedirs(CLEAN_DIR)

# 1. Load the raw data
if os.path.exists(RAW_FILE):
    with open(RAW_FILE, 'r', encoding='utf-8') as f:
        try:
            hymns = json.load(f)
        except Exception as e:
            print(f"Error loading raw JSON: {e}")
            hymns = []
else:
    print("No raw hymns.json found. Exiting.")
    exit()

# Keyword dictionary mapping to your Flutter app's integer system
TYPE_MAP = {
    'intro': 0, 'awal': 0,
    'bait': 1, 'verse': 1,
    'pre-chorus': 2, 'pre chorus': 2,
    'reff': 3, 'chorus': 3, 'korus': 3,
    'bridge': 4, 'jembatan': 4, 'coda': 4, 'ending': 4, 'outro': 4
}

cleaned_hymns = []

for song in hymns:
    # Get the raw lyric string
    raw_text = song.get('lyric', [{}])[0].get('text', '')
    
    # RULE 3: Remove the "Chord [Title] ([Artist])" line at the very beginning
    # This regex looks for a line starting with "Chord" and deletes it + any following blank lines
    raw_text = re.sub(r'^Chord[^\n]+\n+', '', raw_text, flags=re.IGNORECASE).strip()
    
    # RULE 1: Split into chunks by double line breaks (\n\n)
    blocks = re.split(r'\n{2,}', raw_text)
    
    structured_lyrics = []
    current_type = 5 # Default to 'Lyric' if we don't know
    
    for block in blocks:
        block = block.strip()
        if not block:
            continue # Skip empty blocks (Cleanup Rule 7)
            
        lines = block.split('\n')
        first_line_lower = lines[0].strip().lower()
        
        is_header = False
        
        # RULE 2 & 5: Check if the first line is a header (like "Bait :", "Reff 1 :")
        for keyword, type_id in TYPE_MAP.items():
            if first_line_lower.startswith(keyword):
                current_type = type_id # Assign the new type
                is_header = True
                break
                
        if is_header:
            # Strip the header line so "Bait :" doesn't show up in the app UI
            lines = lines[1:]
        # RULE 6: If is_header is False, current_type simply carries over from the last block!
            
        clean_block_text = '\n'.join(lines).strip()
        
        # Only add it if there is still text left after stripping the header
        if clean_block_text:
            structured_lyrics.append({
                "type": current_type,
                "text": clean_block_text
            })
            
    # Rebuild the song object with the new structured lyrics
    cleaned_hymns.append({
        "remote_id": song.get("remote_id"),
        "language": song.get("language"),
        "title": song.get("title"),
        "artist": song.get("artist"),
        "lyric": structured_lyrics
    })

# RULE 4: Sort alphabetically by title
cleaned_hymns = sorted(cleaned_hymns, key=lambda x: x['title'].lower())

# Save the beautifully cleaned JSON
with open(CLEAN_FILE, 'w', encoding='utf-8') as f:
    json.dump(cleaned_hymns, f, ensure_ascii=False, indent=4)

# Update the version file in the cleaned folder
with open(VERSION_FILE, 'w', encoding='utf-8') as f:
    json.dump({"last_updated": int(time.time()), "total_songs": len(cleaned_hymns)}, f, indent=4)

print(f"Pre-processing complete! Cleaned {len(cleaned_hymns)} songs and saved to {CLEAN_DIR}/")
