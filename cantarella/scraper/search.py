#@cantarellabots
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
import asyncio

BASE_URL = "https://aniwatchtv.to"

async def search_anime(query):
    search_url = f"{BASE_URL}/search?keyword={query.replace(' ', '+')}"
    results = []
    try:
        async with async_playwright() as p:
            # Headless mode mein chromium run hoga
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            # URL pe jao aur Cloudflare check ke liye 2 second ruko
            await page.goto(search_url, wait_until="domcontentloaded", timeout=20000)
            await page.wait_for_timeout(2000) 
            
            content = await page.content()
            await browser.close()

        soup = BeautifulSoup(content, 'html.parser')
        
        for item in soup.select('.film_list-wrap .flw-item'):
            title_elem = item.select_one('.film-name a')
            if not title_elem:
                continue
            
            title = title_elem.get('title') or title_elem.text.strip()
            href = title_elem.get('href')
            anime_id = href.split('/')[-1].split('?')[0]
            
            type_elem = item.select_one('.fdi-item')
            anime_type = type_elem.text.strip() if type_elem else "Unknown"

            results.append({
                'title': title,
                'id': anime_id,
                'type': anime_type,
                'url': f"{BASE_URL}{href}" if href.startswith('/') else f"{BASE_URL}/{href}"
            })
            
            if len(results) >= 10:
                break
        return results
    except Exception as e:
        print(f"Playwright Aniwatch Search Error: {e}")
        return []
