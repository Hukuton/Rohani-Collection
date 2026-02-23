import json
import time
import requests
from bs4 import BeautifulSoup
import os
import re

print("Starting JRChord A-Z Scraper...")

# --- 1. THE CHORD MERGER ---
def merge_chords_and_lyrics(raw_text):
    lines = raw_text.split('\n')
    formatted_lines = []
    i = 0
    while i < len(lines):
        line = lines[i].rstrip()
        
        # Regex: Detect if the line is mostly chords (A-G, #, m, dim, sus, etc)
        is_chord_line = re.match(r'^[\sA-Gmb#maj7sus24dim+0-9/()]+$', line) and len(line.strip()) > 0
        
        if is_chord_line and i + 1 < len(lines) and lines[i+1].strip():
            chord_line = line
            lyric_line = lines[i+1].rstrip()
            
            # Pad lyric line with spaces if chords extend further
            if len(chord_line) > len(lyric_line):
                lyric_line += " " * (len(chord_line) - len(lyric_line))
                
            new_line = ""
            last_pos = 0
            
            for match in re.finditer(r'\S+', chord_line):
                chord = match.group()
                pos = match.start()
                
                new_line += lyric_line[last_pos:pos]
                new_line += f"[{chord}]"
                last_pos = pos
            
            new_line += lyric_line[last_pos:]
            formatted_lines.append(new_line.strip())
            i += 2 
        else:
            formatted_lines.append(line)
            i += 1
            
    return "\n".join(formatted_lines).strip()


# --- 2. LOAD EXISTING DATABASE ---
hymns_file = 'hymns.json'
existing_hymns = []
if os.path.exists(hymns_file):
    with open(hymns_file, 'r', encoding='utf-8') as f:
        try:
            existing_hymns = json.load(f)
        except:
            existing_hymns = []

existing_ids = [h.get("remote_id") for h in existing_hymns]
headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}


# --- 3. GET ALL LINKS FROM A-Z PAGES ---
# Using the exact letters you found on the site
letters = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'r', 's', 't', 'u', 'w', 'y', 'z']
all_song_links = []

print("Scanning A-Z directories for links...")
for letter in letters:
    page_url = f"https://www.jrchord.com/judul-lagu-berawal-dari-huruf-{letter}"
    try:
        res = requests.get(page_url, headers=headers)
        soup = BeautifulSoup(res.text, "html.parser")
        
        # Look for the exact div structure from your screenshot
        song_divs = soup.find_all('div', class_=lambda c: c and 'song-responsive' in c)
        for div in song_divs:
            a_tag = div.find('a')
            if a_tag and 'href' in a_tag.attrs:
                href = a_tag['href']
                if href.startswith('/'):
                    all_song_links.append(f"https://www.jrchord.com{href}")
    except Exception as e:
        print(f"Error scanning letter {letter.upper()}: {e}")

# Remove duplicates and filter out songs we already have
all_song_links = list(set(all_song_links))
new_links = [link for link in all_song_links if link.strip('/').split('/')[-1] not in existing_ids]

print(f"Found {len(all_song_links)} total songs. {len(new_links)} are new.")


# --- 4. SCRAPE THE NEW SONGS (Batch of 50) ---
# We scrape 50 at a time so GitHub Actions doesn't time out
for url in new_links[:50]:
    remote_id = url.strip('/').split('/')[-1]
    try:
        r = requests.get(url, headers=headers)
        soup = BeautifulSoup(r.text, "html.parser")
        
        # WE FOUND THE CORRECT TAG! Extracting the <pre> tag
        pre_tag = soup.find("pre")
        if pre_tag:
            raw_text = pre_tag.get_text()
            
            # Format the chords automatically
            final_lyrics = merge_chords_and_lyrics(raw_text)
            
            # Find the title (usually in an h1 tag)
            title_tag = soup.find("h1") or soup.find("title")
            title = title_tag.get_text().split('|')[0].strip() if title_tag else remote_id.replace('-', ' ').title()

            existing_hymns.append({
                "remote_id": remote_id,
                "language": "indo", # Defaulting to indo for jrchord
                "title": title,
                "lyric": [{"type": 5, "text": final_lyrics}]
            })
            print(f"  ✅ Added: {title}")
            time.sleep(1.5) # Polite delay
        else:
            print(f"  ❌ No <pre> tag found on {remote_id}")
            
    except Exception as e:
        print(f"  ⚠️ Error scraping {remote_id}: {e}")


# --- 5. SAVE DATA ---
if len(new_links) > 0:
    with open(hymns_file, 'w', encoding='utf-8') as f:
        json.dump(existing_hymns, f, ensure_ascii=False, indent=4)

    with open('version.json', 'w', encoding='utf-8') as f:
        json.dump({"last_updated": int(time.time())}, f, indent=4)
        
    print(f"\nSuccessfully saved to {hymns_file}!")
else:
    print("\nDatabase is already up to date!")
