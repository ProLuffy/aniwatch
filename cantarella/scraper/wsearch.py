
#@cantarellabots
from cantarella.core.proxy import get_random_proxy, get_proxy_dict
import requests
from bs4 import BeautifulSoup
from curl_cffi import requests as c_requests

BASE_URL = "https://watchanimeworld.net"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://watchanimeworld.net/"
}

def search_animeworld(query):
    search_url = f"{BASE_URL}/?s={query.replace(' ', '+')}"
    try:
        session = c_requests.Session()
        proxy_dict = get_proxy_dict(get_random_proxy())
        if proxy_dict:
            session.proxies.update(proxy_dict)
            
        resp = session.get(search_url, headers=HEADERS, impersonate="chrome", timeout=15)
        if resp.status_code != 200:
            return []

        soup = BeautifulSoup(resp.text, 'html.parser')
        results = []

        for item in soup.select('.result-item, article, .item, .post'):
            a_tag = item.select_one('.title a, h2 a, h3 a, h4 a')
            if not a_tag:
                a_tag = item.select_one('a[href*="/series/"], a[href*="/movies/"]')
            
            if not a_tag:
                continue

            title = a_tag.text.strip() or a_tag.get('title')
            link = a_tag.get('href')

            if title and link and "watchanimeworld.net" in link:
                if not any(x['url'] == link for x in results):
                    # Anime world ka unique ID nikal rahe hain url se
                    anime_id = link.rstrip('/').split('/')[-1]
                    
                    results.append({
                        'title': title,
                        'id': anime_id,
                        'type': "Unknown",
                        'url': link
                    })

            if len(results) >= 10:
                break
                
        return results
    except Exception as e:
        print(f"Search error AnimeWorld: {e}")
        return []
        
