import json
import time
import requests
from bs4 import BeautifulSoup
import os
import re

# --- 1. THE CHORD MERGER (The Magic Part) ---
def merge_chords_and_lyrics(raw_text):
    lines = raw_text.split('\n')
    formatted_lines = []
    i = 0
    
    while i < len(lines):
        line = lines[i].rstrip()
        # Check if this line is a "Chord Line" (mostly spaces and musical notes)
        # Regex looks for A-G chords, minors, and sharps/flats
        is_chord_line = re.match(r'^[\sA-Gmb#maj7sus24dim+0-9/]+$', line)
        
        if is_chord_line and i + 1 < len(lines) and lines[i+1].strip():
            chord_line = line
            lyric_line = lines[i+1]
            new_line = ""
            last_pos = 0
            
            # Find every chord and its position
            for match in re.finditer(r'\S+', chord_line):
                chord = match.group()
                pos = match.start()
                
                # Add text from previous chord to current chord
                new_line += lyric_line[last_pos:pos]
                # Insert the chord in brackets
                new_line += f"[{chord}]"
                last_pos = pos
            
            # Add remaining lyrics
            new_line += lyric_line[last_pos:]
            formatted_lines.append(new_line)
            i += 2 # Skip the lyric line since we merged it
        else:
            formatted_lines.append(line)
            i += 1
            
    return "\n".join(formatted_lines)

# --- 2. LANGUAGE DETECTION ---
def detect_language(text):
    t = text.lower()
    eng = [" the ", " you ", " lord ", " god "]
    ind = [" yang ", " tuhan ", " kau ", " nya "]
    e_score = sum(t.count(w) for w in eng)
    i_score = sum(t.count(w) for w in ind)
    return "en" if e_score > i_score else "indo"

# --- 3. SCRAPER LOGIC ---
hymns_file = 'hymns.json'
existing_hymns = []
if os.path.exists(hymns_file):
    with open(hymns_file, 'r', encoding='utf-8') as f:
        try: existing_hymns = json.load(f)
        except: existing_hymns = []
existing_ids = [h.get("remote_id") for h in existing_hymns]

headers = {"User-Agent": "Mozilla/5.0"}
feed_url = "https://www.jrchord.com/feeds/posts/default?max-results=50"

try:
    res = requests.get(feed_url, headers=headers)
    feed_soup = BeautifulSoup(res.text, 'xml')
    entries = feed_soup.find_all('entry')
    
    for entry in entries:
        link_tag = entry.find('link', rel='alternate')
        if not link_tag: continue
        
        url = link_tag.get('href')
        remote_id = url.strip('/').split('/')[-1]
        
        if remote_id not in existing_ids:
            print(f"Scraping: {remote_id}")
            r = requests.get(url, headers=headers)
            soup = BeautifulSoup(r.text, "html.parser")
            
            lyrics_tag = soup.find("pre")
            if lyrics_tag:
                raw_lyrics = lyrics_tag.get_text()
                
                # RUN THE MERGER HERE!
                final_lyrics = merge_chords_and_lyrics(raw_lyrics)
                
                title_tag = soup.find("h1") or soup.find("title")
                title = title_tag.get_text().split('|')[0].strip() if title_tag else remote_id.replace('-', ' ').title()

                existing_hymns.append({
                    "remote_id": remote_id,
                    "language": detect_language(final_lyrics),
                    "title": title,
                    "lyric": [{"type": 5, "text": final_lyrics}]
                })
                time.sleep(2)

except Exception as e:
    print(f"Error: {e}")

# --- 4. SAVE ---
with open('hymns.json', 'w', encoding='utf-8') as f:
    json.dump(existing_hymns, f, ensure_ascii=False, indent=4)
with open('version.json', 'w', encoding='utf-8') as f:
    json.dump({"last_updated": int(time.time())}, f, indent=4)
