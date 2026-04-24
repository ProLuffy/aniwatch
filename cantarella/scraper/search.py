import requests
from bs4 import BeautifulSoup

def search_anime(query):
    url = f"https://animewatchtv.to/search?keyword={query.replace(' ', '+')}"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    try:
        r = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(r.text, 'html.parser')
        results = []
        for item in soup.select('.film-name a'):
            t = item.get('title') or item.text.strip()
            l = item.get('href')
            results.append({'title': t, 'url': f"https://animewatchtv.to{l}" if l.startswith('/') else l})
        return results[:10]
    except: return []
        
