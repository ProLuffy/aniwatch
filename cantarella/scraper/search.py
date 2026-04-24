#@cantarellabots
from cantarella.core.proxy import get_random_proxy, get_proxy_dict
from bs4 import BeautifulSoup
from curl_cffi import requests as c_requests

BASE_URL = "https://aniwatchtv.to"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
}

def search_anime(query):
    search_url = f"{BASE_URL}/search?keyword={query.replace(' ', '+')}"
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

        # Parse film items
        for item in soup.select('.film_list-wrap .flw-item'):
            title_elem = item.select_one('.film-name a')
            if not title_elem:
                continue
                
            title = title_elem.get('title') or title_elem.text.strip()
            href = title_elem.get('href')
            
            results.append({
                'title': title,
                'url': f"{BASE_URL}{href}" if href.startswith('/') else f"{BASE_URL}/{href}"
            })
            
            if len(results) >= 10:
                break
        
        # Check if the list is empty after successful proxy connection
        if not results:
            return [{'title': 'Error: Proxies working but empty list', 'url': BASE_URL}]
            
        return results
        
    except Exception as e:
        # Catch proxy timeouts or other crashes and send to Telegram UI
        return [{'title': f"Crash Error: {str(e)[:35]}", 'url': BASE_URL}]
        
