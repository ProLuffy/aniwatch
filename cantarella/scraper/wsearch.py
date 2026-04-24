#@cantarellabots
from cantarella.core.proxy import get_random_proxy, get_proxy_dict
from bs4 import BeautifulSoup
from curl_cffi import requests as c_requests

BASE_URL = "https://watchanimeworld.net"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
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
        
        # Return site error directly to the button
        if resp.status_code != 200:
            return [{'title': f"Error: Site returned {resp.status_code}", 'url': BASE_URL}]

        soup = BeautifulSoup(resp.text, 'html.parser')
        results = []

        # Parse articles and posts
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
                    results.append({'title': title, 'url': link})
                    
            if len(results) >= 10:
                break
        
        # Check if the list is empty after successful proxy connection
        if not results:
            return [{'title': 'Error: Proxies working but empty list', 'url': BASE_URL}]
            
        return results
        
    except Exception as e:
        # Catch proxy timeouts or other crashes and send to Telegram UI
        return [{'title': f"Crash Error: {str(e)[:35]}", 'url': BASE_URL}]
        
