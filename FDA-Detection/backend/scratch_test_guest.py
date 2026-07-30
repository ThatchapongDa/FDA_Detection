import httpx
import urllib.parse
import json

async def test_search():
    url = "https://shopee.co.th/api/v4/search/search_items"
    params = {
        "by": "relevancy",
        "keyword": "ยา",
        "limit": 10,
        "newest": 0,
        "order": "desc",
        "page_type": "search",
        "scenario": "PAGE_GLOBAL_SEARCH",
        "version": 2
    }
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Referer": "https://shopee.co.th/search?keyword=%E0%B8%A2%E0%B8%B2",
        "X-Requested-With": "XMLHttpRequest",
        "Accept": "application/json"
    }
    
    print("Testing Guest API Search...")
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.get(url, params=params, headers=headers)
        print(f"Status: {resp.status_code}")
        if resp.status_code == 200:
            data = resp.json()
            items = data.get("items") or []
            print(f"Found {len(items)} items")
            if items:
                print(f"Sample: {items[0].get('item_basic', {}).get('name')}")
        else:
            print(f"Body: {resp.text[:200]}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_search())
