import json
import time
import requests
from bs4 import BeautifulSoup
import os

print("Starting the scraper...")

# =====================================================================
# 1. HELPER FUNCTION: LANGUAGE DETECTION
# =====================================================================
def detect_language(lyrics_text):
    text = lyrics_text.lower()
    
    # Common English and Indonesian words for scoring
    english_keywords = [" the ", " you ", " and ", " lord ", " me ", " my ", " god ", " is "]
    indo_keywords = [" yang ", " tuhan ", " di ", " kau ", " dan ", " ku ", " allah ", " ini "]
    
    english_score = sum(text.count(word) for word in english_keywords)
    indo_score = sum(text.count(word) for word in indo_keywords)
    
    if english_score > indo_score:
        return "en"
    return "indo"

# =====================================================================
# 2. LOAD EXISTING HYMNS FROM GITHUB
# =====================================================================
hymns_file = 'hymns.json'
existing_hymns = []

if os.path.exists(hymns_file):
    with open(hymns_file, 'r', encoding='utf-8') as f:
        try:
            existing_hymns = json.load(f)
        except json.JSONDecodeError:
            existing_hymns = []

# Make a quick list of IDs we already have so we don't scrape them twice
existing_ids = [hymn.get("remote_id") for hymn in existing_hymns]
print(f"Loaded {len(existing_hymns)} existing hymns.")

new_songs_added = 0
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

# =====================================================================
# 3. SCRAPE THE MAIN SONG LIST
# =====================================================================
main_url = "https://www.jrchord.com/daftar-lagu"

try:
    print(f"Fetching main song list from: {main_url}")
    response = requests.get(main_url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # NOTE: You might need to adjust this depending on jrchord's exact HTML.
    # Usually, song lists are just <a> tags inside the main content area.
    song_links = soup.find_all('a') 
    
   # Filter to only keep links that look like actual songs
    valid_links = []
    
    # Words in URLs that we want to IGNORE
    bad_words = ['/p/', 'request', 'tentang', 'contact', 'search', 'label']
    
    for link in song_links:
        href = link.get('href', '')
        
        # 1. It must be a jrchord link
        # 2. It must end with .html (Blogger uses .html for actual song posts)
        if "jrchord.com" in href and href.endswith('.html'):
            
            # 3. It must NOT contain any of our bad words
            if not any(bad_word in href for bad_word in bad_words):
                if href not in valid_links:
                    valid_links.append(href)
            
    print(f"Found {len(valid_links)} potential song links on the page.")

    # =================================================================
    # 4. LOOP THROUGH LINKS AND FETCH NEW SONGS
    # =================================================================
    for song_url in valid_links:
        # Create a unique ID from the URL (e.g. "bagaikan-bejana")
        # Removing trailing slashes first just in case
        remote_id = song_url.strip('/').split('/')[-1]
        
        # Skip if we already have it in our database!
        if remote_id in existing_ids or len(remote_id) < 3:
            continue
            
        print(f"Found NEW song! Fetching: {remote_id}")
        
        try:
            # Visit the specific song page
            song_response = requests.get(song_url, headers=headers)
            song_soup = BeautifulSoup(song_response.text, 'html.parser')
            
            # --- EXTRACT TITLE ---
            # Most blogs use <h1> for the song title
            title_tag = song_soup.find('h1')
            scraped_title = title_tag.text.strip() if title_tag else remote_id.replace('-', ' ').title()
            
            # --- EXTRACT LYRICS ---
            # This targets the main content body where the lyrics usually are.
            # You may need to change 'entry-content' to the specific class jrchord uses.
            content_div = song_soup.find('div', class_='entry-content') or song_soup.find('article')
            
            if content_div:
                raw_lyrics = content_div.text.strip()
            else:
                print(f"  -> Could not find lyrics div for {remote_id}, skipping.")
                continue
                
            # Let the robot figure out the language!
            detected_lang = detect_language(raw_lyrics)
            
            # Format it exactly how your Flutter database expects it
            new_hymn = {
                "remote_id": remote_id,
                "language": detected_lang,
                "title": scraped_title,
                "lyric": [
                    {
                        "type": 5, # 5 = Full Lyric Block in your app
                        "text": raw_lyrics
                    }
                ]
            }
            
            # Add it to our master list
            existing_hymns.append(new_hymn)
            existing_ids.append(remote_id)
            new_songs_added += 1
            
            # BE POLITE! Pause for 2 seconds before hitting their server again
            time.sleep(2)
            
        except Exception as e:
            print(f"  -> Error fetching {remote_id}: {e}")

except Exception as e:
    print(f"An error occurred scraping the main list: {e}")

# =====================================================================
# 5. SAVE THE RESULTS BACK TO GITHUB
# =====================================================================
if new_songs_added > 0:
    print(f"\nSuccess! Added {new_songs_added} new songs.")
    
    # 1. Save the giant list of hymns
    with open('hymns.json', 'w', encoding='utf-8') as f:
        # ensure_ascii=False keeps special characters (like é, ä, etc) intact
        json.dump(existing_hymns, f, ensure_ascii=False, indent=4)
    
    # 2. Save the timestamp so your Flutter app knows there is an update
    version_data = {"last_updated": int(time.time())}
    with open('version.json', 'w', encoding='utf-8') as f:
        json.dump(version_data, f, indent=4)
        
    print("Successfully updated hymns.json and version.json!")
else:
    print("\nNo new songs found. Everything is already up to date.")
