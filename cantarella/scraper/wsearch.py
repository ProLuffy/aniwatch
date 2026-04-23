#@cantarellabots
from curl_cffi import requests
from bs4 import BeautifulSoup
import urllib.parse

def search_animeworld(query):
    query = urllib.parse.quote(query)
    url = f"https://watchanimeworld.net/?s={query}"
    try:
        r = requests.get(url, impersonate="chrome", timeout=15)
        soup = BeautifulSoup(r.text, 'html.parser')
        results = []

        for article in soup.find_all(['article', 'div'], class_=['post', 'item', 'result-item', 'type-post']):
            a_tag = article.find('a')
            if not a_tag:
                continue
            title = a_tag.get('title') or a_tag.text.strip()
            link = a_tag.get('href')
            
            if title and link and "watchanimeworld.net" in link:
                if link not in [x['url'] for x in results]:
                    results.append({'title': title, 'url': link})
            if len(results) >= 10:
                break
        return results
    except Exception as e:
        print(f"Scraper Error AnimeWorld: {e}")
        return []
