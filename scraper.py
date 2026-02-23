def get_all_links():
    headers = {"User-Agent": "Mozilla/5.0"}
    # These are the specific XML files you found that contain the songs
    sitemaps = [
        "https://www.jrchord.com/post-sitemap.xml",
        "https://www.jrchord.com/post-sitemap2.xml"
    ]
    all_links = []
    
    for s_url in sitemaps:
        try:
            print(f"Checking sitemap: {s_url}")
            r = requests.get(s_url, headers=headers)
            # Use 'xml' parser specifically for sitemaps
            soup = BeautifulSoup(r.text, 'xml')
            
            # Extract all <loc> tags from these specific files
            links = [loc.text for loc in soup.find_all('loc')]
            print(f"  Found {len(links)} links in this file.")
            all_links.extend(links)
        except Exception as e:
            print(f"  Error reading {s_url}: {e}")
            
    return list(set(all_links)) # This removes any duplicates
