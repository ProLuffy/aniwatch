#@cantarellabots
from curl_cffi import requests
from bs4 import BeautifulSoup
import urllib.parse

def search_animeworld(query):
    # Query ko URL ke liye safe format mein convert kar rahe hain
    query = urllib.parse.quote(query)
    url = f"https://watchanimeworld.net/?s={query}"
    
    # Headers add kiye taaki site ko lage real Chrome browser hai
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://watchanimeworld.net/"
    }
    
    try:
        r = requests.get(url, headers=headers, impersonate="chrome", timeout=15)
        soup = BeautifulSoup(r.text, 'html.parser')
        results = []

        # Site ke main result containers ko target kar rahe hain
        for item in soup.select('.result-item, article, .item, .post'):
            # Sabse pehle title (Heading) ke andar wala link dhundo
            a_tag = item.select_one('.title a, h2 a, h3 a, h4 a')
            
            # Agar heading nahi mili, toh direct /series/ ya /movies/ wala link dhundo
            if not a_tag:
                a_tag = item.select_one('a[href*="/series/"], a[href*="/movies/"]')

            if not a_tag:
                continue

            title = a_tag.text.strip() or a_tag.get('title')
            link = a_tag.get('href')

            # Agar link valid hai aur title exist karta hai
            if title and link and "watchanimeworld.net" in link:
                # Same link do baar na aaye isliye duplicate check
                if not any(x['url'] == link for x in results):
                    results.append({'title': title, 'url': link})

            # Max 10 results taaki button limit cross na ho
            if len(results) >= 10:
                break
                
        return results
    except Exception as e:
        print(f"Scraper Error AnimeWorld: {e}")
        return []
