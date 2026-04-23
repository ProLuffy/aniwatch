#@cantarellabots
from curl_cffi import requests
from bs4 import BeautifulSoup
import urllib.parse

def search_anime(query):
    query = urllib.parse.quote(query)
    # Using animewatchtv.to as you requested
    url = f"https://animewatchtv.to/search?keyword={query}" 
    try:
        r = requests.get(url, impersonate="chrome", timeout=15)
        soup = BeautifulSoup(r.text, 'html.parser')
        results = []
        
        for item in soup.select('.film-name a'):
            title = item.get('title') or item.text.strip()
            link = item.get('href')
            if title and link:
                full_link = f"https://animewatchtv.to{link}" if link.startswith('/') else link
                results.append({'title': title, 'url': full_link})
            if len(results) >= 10:
                break
        return results
    except Exception as e:
        print(f"Scraper Error Aniwatch: {e}")
        return []
