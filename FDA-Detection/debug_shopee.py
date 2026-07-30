import asyncio
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        page = await context.new_page()
        url = "https://shopee.co.th/Paracap-Paracetamol-Tablets-500mg.-%E0%B8%9E%E0%B8%B2%E0%B8%A3%E0%B8%B2%E0%B9%81%E0%B8%84%E0%B8%9E-%E0%B8%9E%E0%B8%B2%E0%B8%A3%E0%B8%B2%E0%B9%80%E0%B8%8B%E0%B8%95%E0%B8%B2%E0%B8%A1%E0%B8%AD%E0%B8%A5-500-%E0%B8%A1%E0%B8%B4%E0%B8%A5%E0%B8%A5%E0%B8%B4%E0%B8%81%E0%B8%A3%E0%B8%B1%E0%B8%A1-10-%E0%B9%80%E0%B8%A1%E0%B9%87%E0%B8%94-50-%E0%B9%81%E0%B8%9C%E0%B8%87-1-%E0%B8%81%E0%B8%A5%E0%B9%88%E0%B8%AD%E0%B8%87-FF-6301-%E0%B8%A2%E0%B8%B2%E0%B8%AA%E0%B8%B2%E0%B8%A1%E0%B8%B1%E0%B8%8D%E0%B8%9B%E0%B8%A3%E0%B8%B0%E0%B8%88%E0%B8%B3%E0%B8%9A%E0%B9%89%E0%B8%B2%E0%B8%99-i.97475696.26650534704"
        print(f"Navigating to {url}...")
        await page.goto(url, wait_until="networkidle")
        await asyncio.sleep(5)
        title = await page.title()
        print(f"Page Title: {title}")
        content = await page.content()
        with open("shopee_debug.html", "w", encoding="utf-8") as f:
            f.write(content)
        await browser.close()

asyncio.run(run())
