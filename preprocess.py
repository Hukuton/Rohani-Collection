import json
import os
import re
import time

print("Starting Data Pre-Processing...")

RAW_FILE = 'hymns.json'
CLEAN_DIR = 'cleaned'
CLEAN_FILE = os.path.join(CLEAN_DIR, 'hymn.json')
VERSION_FILE = os.path.join(CLEAN_DIR, 'version.json')

if not os.path.exists(CLEAN_DIR):
    os.makedirs(CLEAN_DIR)

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

# UPDATED DICTIONARY TO MATCH YOUR NEW 0-5 FLUTTER MAPPING
TYPE_MAP = {
    'intro': 0, 'awal': 0,
    'bait': 1, 'verse': 1,
    'pre-chorus': 2, 'pre chorus': 2,
    'reff': 3, 'chorus': 3, 'korus': 3,
    'bridge': 4, 'jembatan': 4,
    'outro': 5, 'coda': 5, 'ending': 5, 'akhiran': 5
}

cleaned_hymns = []

for song in hymns:
    raw_text = song.get('lyric', [{}])[0].get('text', '')
    
    # Strip the redundant "Chord Title (Artist)" header line
    raw_text = re.sub(r'^Chord[^\n]+\n+', '', raw_text, flags=re.IGNORECASE).strip()
    
    blocks = re.split(r'\n{2,}', raw_text)
    
    structured_lyrics = []
    current_type = 1 # DEFAULT IS NOW VERSE (1) INSTEAD OF 5!
    
    for block in blocks:
        block = block.strip()
        if not block:
            continue 
            
        lines = block.split('\n')
        first_line_lower = lines[0].strip().lower()
        
        is_header = False
        
        for keyword, type_id in TYPE_MAP.items():
            if first_line_lower.startswith(keyword):
                current_type = type_id 
                is_header = True
                break
                
        if is_header:
            lines = lines[1:] # Remove the "Bait :" header line so it doesn't show in app
            
        clean_block_text = '\n'.join(lines).strip()
        
        if clean_block_text:
            structured_lyrics.append({
                "type": current_type,
                "text": clean_block_text
            })
            
    cleaned_hymns.append({
        "remote_id": song.get("remote_id"),
        "language": song.get("language"),
        "title": song.get("title"),
        "artist": song.get("artist"),
        "key": song.get("key", ""), # PRESERVES THE KEY!
        "lyric": structured_lyrics
    })

# Sort alphabetically by title so your JSON is neat
cleaned_hymns = sorted(cleaned_hymns, key=lambda x: x['title'].lower())

with open(CLEAN_FILE, 'w', encoding='utf-8') as f:
    json.dump(cleaned_hymns, f, ensure_ascii=False, indent=4)

with open(VERSION_FILE, 'w', encoding='utf-8') as f:
    json.dump({"last_updated": int(time.time()), "total_songs": len(cleaned_hymns)}, f, indent=4)

print(f"Pre-processing complete! Cleaned {len(cleaned_hymns)} songs and saved to {CLEAN_DIR}/")
