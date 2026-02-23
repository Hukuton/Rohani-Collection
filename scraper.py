import json
import time
import requests
from bs4 import BeautifulSoup
import os
import re

# --- 1. THE CHORD MERGER ---
def merge_chords_and_lyrics(raw_text):
    lines = raw_text.split('\n')
    formatted_lines = []
    i = 0
    while i < len(lines):
        line = lines[i].rstrip()
        # Detect if it's a chord line (Letters A-G, #, m, 7, etc.)
        is_chord_line = re.match(r'^[\sA-Gmb#maj7sus24dim+0-9/]+$', line)
        
        if is_chord_line and i + 1 < len(lines) and lines[i+1].strip():
            chord_line = line
            lyric_line = lines[i+1]
            new_line = ""
            last_pos = 0
            for match in re.finditer(r'\S+', chord_line):
                chord = match.group()
                pos = match.start()
                new_line += lyric_line[last_pos:pos]
                new_line += f"[{chord}]"
                last_pos = pos
            new_line += lyric_line[last_pos:]
            formatted_lines.append(new_line)
            i += 2 
        else:
            formatted_lines.append(line)
            i += 1
    return "\n".join(formatted_lines)

# --- 2. LOAD EXISTING DATA ---
hymns_file = 'hymns.json'
existing_hymns = []
if os.path.exists(hymns_file):
    with open(hymns_file, 'r', encoding='utf-8') as f:
        try: existing_hymns = json.load(f)
        except: existing_hymns = []
existing_ids = [h.get("remote_id") for h in existing_hymns]

# --- 3. CRAWL THE SITEMAP TO FIND URLS ---
sitemap_url = "https://www.jrchord.com/sitemap.xml"
headers = {"User-Agent": "Mozilla/5.0"}
links_to_scrape = []

print("Reading sitemap...")
try:
    s_res = requests.get(sitemap_url, headers=headers)
    s_soup = BeautifulSoup(s_res.text, 'xml')
    # Find all <loc> tags that end in .html and aren't static pages (/p/)
    all_locs = [loc.text for loc in s_soup.find_all('loc')]
    for url in all_locs:
        if url.endswith('.html') and '/p/' not in url:
            remote_id = url.strip('/').split('/')[-1]
            if remote_id not in existing_ids:
                links_to_scrape.append(url)
except Exception as e:
    print(f"Sitemap error: {e}")

print(f"Found {len(links_to_scrape)} new songs to scrape.")

# --- 4. SCRAPE INDIVIDUAL SONGS ---
# Limiting to 20 per run so GitHub Actions doesn't time out
for url in links_to_scrape[:20]:
    remote_id = url.strip('/').split('/')[-1]
    print(f"Scraping: {remote_id}")
    try:
        r = requests.get(url, headers=headers)
        soup = BeautifulSoup(r.text, "html.parser")
        
        # Use your confirmed working <pre> logic
        lyrics_tag = soup.find("pre")
        if lyrics_tag:
            raw_text = lyrics_tag.get_text()
            final_lyrics = merge_chords_and_lyrics(raw_text)
            
            title_tag = soup.find("h1") or soup.find("title")
            title = title_tag.get_text().split('|')[0].strip() if title_tag else remote_id.replace('-', ' ').title()

            existing_hymns.append({
                "remote_id": remote_id,
                "language": "indo", # Default for this site
                "title": title,
                "lyric": [{"type": 5, "text": final_lyrics}]
            })
            time.sleep(2) # Be polite
    except Exception as e:
        print(f"Error on {url}: {e}")

# --- 5. SAVE ---
with open('hymns.json', 'w', encoding='utf-8') as f:
    json.dump(existing_hymns, f, ensure_ascii=False, indent=4)
with open('version.json', 'w', encoding='utf-8') as f:
    json.dump({"last_updated": int(time.time())}, f, indent=4)
