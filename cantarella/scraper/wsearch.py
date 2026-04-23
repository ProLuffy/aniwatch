#@cantarellabots
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

BASE_URL = "https://watchanimeworld.net"

async def search_animeworld(query):
    search_url = f"{BASE_URL}/?s={query.replace(' ', '+')}"
    results = []
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            await page.goto(search_url, wait_until="domcontentloaded", timeout=20000)
            await page.wait_for_timeout(2000)
            
            content = await page.content()
            await browser.close()

        soup = BeautifulSoup(content, 'html.parser')

        for item in soup.select('article, .item, .result-item, .post'):
            title_elem = item.select_one('h2 a, h3 a, .title a, a')
            if not title_elem:
                continue

            title = title_elem.text.strip() or title_elem.get('title')
            href = title_elem.get('href')

            if title and href and ("/" in href):
                results.append({
                    'title': title,
                    'url': href if href.startswith('http') else f"{BASE_URL}{href}",
                    'id': href.split('/')[-2] if href.endswith('/') else href.split('/')[-1]
                })

            if len(results) >= 10:
                break
        return results
    except Exception as e:
        print(f"AnimeWorld Search Error: {e}")
        return []
