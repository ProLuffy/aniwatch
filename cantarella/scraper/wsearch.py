import requests
from bs4 import BeautifulSoup

def search_animeworld(query):
    url = f"https://watchanimeworld.net/?s={query.replace(' ', '+')}"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    try:
        r = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(r.text, 'html.parser')
        results = []
        for a in soup.select('.result-item a, article a, .item a'):
            title = a.get('title') or a.text.strip()
            link = a.get('href')
            if title and link and "watchanimeworld.net" in link and not any(x['url'] == link for x in results):
                results.append({'title': title, 'url': link})
        return results[:10]
    except: return []
        
