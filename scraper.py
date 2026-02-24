import json
import time
import requests
from bs4 import BeautifulSoup
import os
import re

print("Starting JRChord A-Z Scraper...")

def merge_chords_and_lyrics(raw_text):
    lines = raw_text.split('\n')
    formatted_lines = []
    i = 0
    while i < len(lines):
        line = lines[i].rstrip()
        is_chord_line = re.match(r'^[\sA-Gmb#maj7sus24dim+0-9/()]+$', line) and len(line.strip()) > 0
        
        if is_chord_line and i + 1 < len(lines) and lines[i+1].strip():
            chord_line = line
            lyric_line = lines[i+1].rstrip()
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

def detect_language(text):
    t = text.lower()
    eng = [" the ", " you ", " and ", " lord ", " god ", " of ", " in ", " me ", " my ", " is "]
    ind = [" yang ", " tuhan ", " kau ", " dan ", " nya ", " di ", " ini ", " ku ", " allah "]
    e_score = sum(t.count(w) for w in eng)
    i_score = sum(t.count(w) for w in ind)
    return "en" if e_score > i_score else "indo"

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

letters = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'r', 's', 't', 'u', 'w', 'y', 'z']
all_song_links = []

print("Scanning A-Z directories for links...")
for letter in letters:
    page_url = f"https://www.jrchord.com/judul-lagu-berawal-dari-huruf-{letter}"
    try:
        res = requests.get(page_url, headers=headers)
        soup = BeautifulSoup(res.text, "html.parser")
        song_divs = soup.find_all('div', class_=lambda c: c and 'song-responsive' in c)
        for div in song_divs:
            a_tag = div.find('a')
            if a_tag and 'href' in a_tag.attrs:
                href = a_tag['href']
                if href.startswith('/'):
                    all_song_links.append(f"https://www.jrchord.com{href}")
    except Exception as e:
        print(f"Error scanning letter {letter.upper()}: {e}")

all_song_links = list(set(all_song_links))
new_links = [link for link in all_song_links if link.strip('/').split('/')[-1] not in existing_ids]

print(f"Found {len(all_song_links)} total songs. {len(new_links)} are new.")

for url in new_links[:100]:
    remote_id = url.strip('/').split('/')[-1]
    try:
        r = requests.get(url, headers=headers)
        soup = BeautifulSoup(r.text, "html.parser")
        
        pre_tag = soup.find("pre")
        if pre_tag:
            raw_text = pre_tag.get_text()
            original_key = pre_tag.get("data-key", "") # GRAB THE KEY!
            
            final_lyrics = merge_chords_and_lyrics(raw_text)
            detected_lang = detect_language(final_lyrics)
            
            title_tag = soup.find("h1", class_="song-detail-title")
            clean_title = title_tag.get_text().strip() if title_tag else remote_id.replace('-', ' ').title()
            
            artist_tag = soup.find("div", class_="song-detail-artist")
            artist = artist_tag.get_text().strip() if artist_tag else ""

            existing_hymns.append({
                "remote_id": remote_id,
                "language": detected_lang,
                "title": clean_title,
                "artist": artist,
                "key": original_key, # SAVE THE KEY!
                "lyric": [{"type": 5, "text": final_lyrics}] # Temp type 5, Preprocessor will fix this
            })
            print(f"  ✅ Added: {clean_title} by {artist} [{detected_lang.upper()}] (Key: {original_key})")
            time.sleep(1.5) 
        else:
            print(f"  ❌ No <pre> tag found on {remote_id}")
            
    except Exception as e:
        print(f"  ⚠️ Error scraping {remote_id}: {e}")

if len(new_links) > 0:
    with open(hymns_file, 'w', encoding='utf-8') as f:
        json.dump(existing_hymns, f, ensure_ascii=False, indent=4)
    with open('version.json', 'w', encoding='utf-8') as f:
        json.dump({"last_updated": int(time.time())}, f, indent=4)
    print(f"\nSuccessfully saved {len(existing_hymns)} total songs to {hymns_file}!")
else:
    print("\nDatabase is already up to date!")
