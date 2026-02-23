import json
import time
import requests
from bs4 import BeautifulSoup
import os
import re

# --- 1. THE CHORD MERGER (Converts separate lines to [G] format) ---
def merge_chords_and_lyrics(raw_text):
    lines = raw_text.split('\n')
    formatted_lines = []
    i = 0
    while i < len(lines):
        line = lines[i].rstrip()
        # Regex to detect a "Chord Line" (A-G, sharps, minors, etc.)
        is_chord_line = re.match(r'^[\sA-Gmb#maj7sus24dim+0-9/]+$', line)
        
        # If this is a chord line and the next line has lyrics
        if is_chord_line and i + 1 < len(lines) and lines[i+1].strip():
            chord_line = line
            lyric_line = lines[i+1]
            new_line = ""
            last_pos = 0
            
            # Find every chord and its character index
            for match in re.finditer(r'\S+', chord_line):
                chord = match.group()
                pos = match.start()
                
                # Merge: lyrics up to the chord + the chord in brackets
                new_line += lyric_line[last_pos:pos]
                new_line += f"[{chord}]"
                last_pos = pos
            
            new_line += lyric_line[last_pos:]
            formatted_lines.append(new_line)
            i += 2 # Skip the lyric line since we merged it
        else:
            formatted_lines.append(line)
            i += 1
    return "\n".join(formatted_lines)

# --- 2. THE SITEMAP CRAWLER (Uses the "Gold Mine" URLs) ---
def get_all_links():
    headers = {"User-Agent": "Mozilla/5.0"}
    sitemaps = [
        "https://www.jrchord.com/post-sitemap.xml",
        "https://www.jrchord.com/post-sitemap2.xml"
    ]
    all_links = []
    for s_url in sitemaps:
        try:
            print(f"Checking sitemap: {s_url}")
            r = requests.get(s_url, headers=headers)
            soup = BeautifulSoup(r.text, 'xml')
            # Extract all URLs ending in .html
            links = [loc.text for loc in soup.find_all('loc') if loc.text.endswith('.html')]
            print(f"  Found {len(links)} links.")
            all_links.extend(links)
        except Exception as e:
            print(f"  Error reading {s_url}: {e}")
    return list(set(all_links))

# --- 3. MAIN SCRAPING ENGINE ---
hymns_file = 'hymns.json'
existing_hymns = []
if os.path.exists(hymns_file):
    with open(hymns_file, 'r', encoding='utf-8') as f:
        try:
            existing_hymns = json.load(f)
        except:
            existing_hymns = []

existing_ids = [h.get("remote_id") for h in existing_hymns]
all_links = get_all_links()
new_links = [l for l in all_links if l.strip('/').split('/')[-1] not in existing_ids]

print(f"Found {len(new_links)} new songs to scrape. Starting batch of 50...")

# Scrape 50 per run to stay within GitHub Action time limits
for url in new_links[:50]:
    remote_id = url.strip('/').split('/')[-1]
    try:
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(r.text, "html.parser")
        
        # Using the <pre> tag discovery
        lyrics_tag = soup.find("pre")
        if lyrics_tag:
            raw_text = lyrics_tag.get_text()
            final_lyrics = merge_chords_and_lyrics(raw_text)
            
            title_tag = soup.find("h1") or soup.find("title")
            title = title_tag.get_text().split('|')[0].strip()

            existing_hymns.append({
                "remote_id": remote_id,
                "language": "indo", # Defaulting as jrchord is mainly indo
                "title": title,
                "lyric": [{"type": 5, "text": final_lyrics}]
            })
            print(f"  Successfully added: {title}")
            time.sleep(2) # Politeness delay
    except Exception as e:
        print(f"  Error on {url}: {e}")

# --- 4. SAVE AND TIMESTAMP ---
with open(hymns_file, 'w', encoding='utf-8') as f:
    json.dump(existing_hymns, f, ensure_ascii=False, indent=4)

with open('version.json', 'w', encoding='utf-8') as f:
    json.dump({"last_updated": int(time.time())}, f, indent=4)

print("Update complete.")
