## +++ Made By Obito [@i_killed_my_clan] +++


from cantarella.core.proxy import get_random_proxy, get_proxy_dict
from bs4 import BeautifulSoup
from curl_cffi import requests

BASE_URL = "https://watchanimeworld.net"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
}

def search_animeworld(query):
    # Typically WordPress/streaming sites use ?s=query
    search_url = f"{BASE_URL}/?s={query.replace(' ', '+')}"
    
    try:
        session = requests.Session()
        proxy_dict = get_proxy_dict(get_random_proxy())
        if proxy_dict:
            session.proxies.update(proxy_dict)
            
        resp = session.get(search_url, headers=HEADERS, impersonate="chrome")
        if resp.status_code != 200:
            return []

        soup = BeautifulSoup(resp.text, 'html.parser')
        results = []

        # Looking for standard post/item containers on anime sites
        for item in soup.select('article, .item, .result-item, .post'):
            # Looking for the title inside anchor tags
            title_elem = item.select_one('h2 a, h3 a, .title a, a')
            if not title_elem:
                continue

            title = title_elem.text.strip() or title_elem.get('title')
            href = title_elem.get('href')

            # Ensure we only pick valid links
            if title and href and ("/" in href):
                results.append({
                    'title': title,
                    'url': href if href.startswith('http') else f"{BASE_URL}{href}",
                    'id': href.split('/')[-2] if href.endswith('/') else href.split('/')[-1]
                })

            # Limit to 10 to prevent massive inline keyboards
            if len(results) >= 10:
                break

        return results
    except Exception as e:
        print(f"WatchAnimeWorld Search Error: {e}")
        return []
      
