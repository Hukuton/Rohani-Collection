import json
import time
import requests
from bs4 import BeautifulSoup
import os
import re

# --- 1. CHORD MERGER LOGIC ---
def merge_chords_and_lyrics(raw_text):
    lines = raw_text.split('\n')
    formatted_lines = []
    i = 0
    while i < len(lines):
        line = lines[i].rstrip()
        # Detect if it's a chord line
        is_chord_line = re.match(r'^[\sA-Gmb#maj7sus24dim+0-9/]+$', line)
        if is_chord_line and i + 1 < len(lines) and lines[i+1].strip():
            chord_line, lyric_line = line, lines[i+1]
            new_line, last_pos = "", 0
            for match in re.finditer(r'\S+', chord_line):
                chord, pos = match.group(), match.start()
                new_line += lyric_line[last_pos:pos] + f"[{chord}]"
                last_pos = pos
            new_line += lyric_line[last_pos:]
            formatted_lines.append(new_line)
            i += 2 
        else:
            formatted_lines.append(line)
            i += 1
    return "\n".join(formatted_lines)

# --- 2. CRAWL MULTIPLE SITEMAPS ---
def get_all_links():
    headers = {"User-Agent": "Mozilla/5.0"}
    # Blogger often uses indexed sitemaps. We check the main one and common post sitemaps.
    sitemaps = [
        "https://www.jrchord.com/sitemap.xml",
        "https://www.jrchord.com/sitemap-posts-1.xml"
    ]
    all_links = []
    for s_url in sitemaps:
        try:
            print(f"Checking sitemap: {s_url}")
            r = requests.get(s_url, headers=headers)
            soup = BeautifulSoup(r.text, 'xml')
            links = [loc.text for loc in soup.find_all('loc') if loc.text.endswith('.html') and '/p/' not in loc.text]
            all_links.extend(links)
        except: pass
    return list(set(all_links)) # Remove duplicates

# --- 3. MAIN RUN ---
hymns_file = 'hymns.json'
existing_hymns = []
if os.path.exists(hymns_file):
    with open(hymns_file, 'r', encoding='utf-8') as f:
        try: existing_hymns = json.load(f)
        except: existing_hymns = []
existing_ids = [h.get("remote_id") for h in existing_hymns]

new_links = [l for l in get_all_links() if l.strip('/').split('/')[-1] not in existing_ids]
print(f"Found {len(new_links)} new songs to scrape.")

# Scrape 20 at a time to stay safe
for url in new_links[:20]:
    remote_id = url.strip('/').split('/')[-1]
    try:
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(r.text, "html.parser")
        lyrics_tag = soup.find("pre")
        if lyrics_tag:
            final_lyrics = merge_chords_and_lyrics(lyrics_tag.get_text())
            title_tag = soup.find("h1") or soup.find("title")
            title = title_tag.get_text().split('|')[0].strip()
            existing_hymns.append({
                "remote_id": remote_id, "language": "indo", "title": title,
                "lyric": [{"type": 5, "text": final_lyrics}]
            })
            print(f"  Added: {title}")
            time.sleep(2)
    except Exception as e: print(f"  Error: {e}")

# Save results
with open(hymns_file, 'w', encoding='utf-8') as f:
    json.dump(existing_hymns, f, ensure_ascii=False, indent=4)
with open('version.json', 'w', encoding='utf-8') as f:
    json.dump({"last_updated": int(time.time())}, f, indent=4)
