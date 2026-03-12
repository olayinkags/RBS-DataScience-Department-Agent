import re
import asyncio
import random
import time
import json
import os
import requests
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup

URLS = {
    "nigeria": [
        "https://romebusinessschool.ng/executive-master-in-data-science/",
    ],
    "italy": [
        "https://romebusinessschool.com/master-in-data-science-executive/",
    ]
}

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
]


def clean_text(text: str) -> str:
    """Remove excessive whitespace and junk from scraped text."""
    # Remove lines that are just whitespace
    lines = [line.strip() for line in text.split('\n')]
    lines = [line for line in lines if line]  # Remove empty lines
    
    # Remove duplicate consecutive lines (navigation menus repeat)
    deduped = []
    prev = None
    for line in lines:
        if line != prev:
            deduped.append(line)
        prev = line
    
    text = '\n'.join(deduped)
    
    # Collapse 3+ newlines into 2
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    return text.strip()



async def scrape_with_playwright(url: str) -> str:
    """
    Scrape using Playwright with stealth settings to avoid bot detection.
    
    Key stealth techniques:
    - Random realistic User-Agent
    - Proper browser headers
    - Override navigator.webdriver (the main bot detection flag)
    - Human-like mouse movement and scroll
    - Random delays
    """
    user_agent = random.choice(USER_AGENTS)
    
    async with async_playwright() as p:
        # Launch with args that make it look more like a real browser
        browser = await p.chromium.launch(
            headless=True,
            args=[
                '--no-sandbox',
                '--disable-blink-features=AutomationControlled',  # KEY: hides automation
                '--disable-infobars',
                '--disable-dev-shm-usage',
                '--disable-extensions',
                '--no-first-run',
                '--ignore-certificate-errors',
            ]
        )
        
        # Create browser context with realistic settings
        context = await browser.new_context(
            user_agent=user_agent,
            viewport={"width": 1366, "height": 768},  # Common screen resolution
            locale="en-US",
            timezone_id="Africa/Lagos",  # Timezone appropriate for Nigeria
            # Simulate a real browser's accepted content
            extra_http_headers={
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "Accept-Encoding": "gzip, deflate, br",
                "DNT": "1",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "none",
                "Sec-Fetch-User": "?1",
                "Cache-Control": "max-age=0",
            }
        )
        
        page = await context.new_page()
        
        # CRITICAL: Override JavaScript properties that reveal automation
        # navigator.webdriver = true is the main flag websites check
        await page.add_init_script("""
            // Hide webdriver flag
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
                configurable: true
            });
            
            // Make plugins list non-empty (empty = bot)
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5],
                configurable: true
            });
            
            // Set realistic language settings
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en'],
                configurable: true
            });
            
            // Override chrome object to look real
            window.chrome = {
                runtime: {},
                loadTimes: function() {},
                csi: function() {},
                app: {}
            };
            
            // Fix permissions query (bots often fail this)
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                    Promise.resolve({ state: Notification.permission }) :
                    originalQuery(parameters)
            );
        """)
        
        print(f"    → Navigating to page...")
        
        try:
            # Navigate to the URL
            # domcontentloaded is less strict than networkidle — works better
            # for sites with anti-bot protection
            response = await page.goto(
                url,
                wait_until="domcontentloaded",
                timeout=45000
            )
            
            # Check if we got a 403
            if response and response.status == 403:
                print(f"    ✗ Got 403 from Playwright, will try requests fallback...")
                await browser.close()
                return None  # Signal to try fallback
            
            # Wait a bit more for dynamic content to load
            await asyncio.sleep(random.uniform(2, 4))  # Human-like delay
            
            # Simulate scrolling (some sites only load content when scrolled to)
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight / 2)")
            await asyncio.sleep(1)
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await asyncio.sleep(1)
            
            # Get the rendered HTML
            content = await page.content()
            
        except Exception as e:
            print(f"    ✗ Playwright navigation error: {e}")
            await browser.close()
            return None
        
        await browser.close()
    
    # Parse and clean
    soup = BeautifulSoup(content, "html.parser")
    
    # Remove irrelevant HTML elements
    for tag in soup(["nav", "footer", "script", "style", "header",
                     "noscript", "iframe", "aside", "form",
                     ".cookie-banner", ".popup", ".modal"]):
        tag.decompose()
    
    text = soup.get_text(separator="\n", strip=True)
    return clean_text(text)


def scrape_with_requests(url: str) -> str:
    """
    Fallback scraper using requests library with real browser headers.
    Faster than Playwright but can't execute JavaScript.
    """
    user_agent = random.choice(USER_AGENTS)
    
    session = requests.Session()
    
    headers = {
        "User-Agent": user_agent,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Cache-Control": "max-age=0",
        "Referer": "https://www.google.com/",  # Pretend we came from Google
    }
    
    # First visit the homepage to get cookies (like a real user would)
    try:
        base_url = '/'.join(url.split('/')[:3])  # e.g., https://romebusinessschool.ng
        print(f"    → Getting homepage cookies first: {base_url}")
        session.get(base_url, headers=headers, timeout=15)
        time.sleep(random.uniform(1, 2))  # Pause like a human
    except Exception:
        pass  # Continue even if homepage fails
    
    print(f"    → Fetching target page...")
    response = session.get(url, headers=headers, timeout=30)
    
    if response.status_code == 403:
        raise Exception(f"403 Forbidden — even requests library blocked")
    
    if response.status_code != 200:
        raise Exception(f"HTTP {response.status_code} error")
    
    # Parse HTML
    soup = BeautifulSoup(response.text, "html.parser")
    
    # Remove irrelevant elements
    for tag in soup(["nav", "footer", "script", "style", "header",
                     "noscript", "iframe", "aside", "form"]):
        tag.decompose()
    
    text = soup.get_text(separator="\n", strip=True)
    return clean_text(text)


def get_manual_content(url: str, campus: str) -> str:
    """
    Prompt user to manually provide page content.
    Use this when automated scraping is blocked.
    
    Instructions for manual collection:
    1. Open the URL in your browser
    2. Press Ctrl+A to select all text, then Ctrl+C to copy
    3. OR: Right-click → View Page Source → Ctrl+A → Ctrl+C
    4. Paste it when prompted below
    """
    print(f"\n{'='*60}")
    print(f"MANUAL INPUT NEEDED FOR: {url}")
    print(f"{'='*60}")
    print("Automated scraping was blocked. Please:")
    print(f"  1. Open this URL in your browser: {url}")
    print("  2. Select ALL text on the page (Ctrl+A)")
    print("  3. Copy it (Ctrl+C)")
    print("  4. Come back here and paste it (Ctrl+V)")
    print("  5. Press Enter twice when done")
    print("  (Or type 'SKIP' to skip this page)")
    print(f"{'='*60}\n")
    
    lines = []
    try:
        while True:
            line = input()
            if line == "SKIP":
                return ""
            if line == "" and lines and lines[-1] == "":
                break
            lines.append(line)
    except EOFError:
        pass
    
    content = '\n'.join(lines).strip()
    print(f"  ✓ Received {len(content)} characters of manual content")
    return content

async def scrape_page(url: str, campus: str) -> str:
    """
    Try multiple scraping methods in order. Return first successful result.
    
    Order: Playwright (stealth) → requests → manual input
    """
    
    # Attempt 1: Playwright with stealth
    print(f"    Method 1: Playwright stealth browser...")
    try:
        result = await scrape_with_playwright(url)
        if result and len(result) > 500 and "403" not in result[:100]:
            print(f"    ✓ Playwright succeeded ({len(result):,} chars)")
            return result
        else:
            print(f"    ✗ Playwright got blocked or returned too little content")
    except Exception as e:
        print(f"    ✗ Playwright failed: {e}")
    
    # Brief pause before trying next method
    await asyncio.sleep(2)
    
    # Attempt 2: requests library
    print(f"    Method 2: requests with browser headers...")
    try:
        result = scrape_with_requests(url)
        if result and len(result) > 500 and "403" not in result[:100]:
            print(f"    ✓ Requests succeeded ({len(result):,} chars)")
            return result
        else:
            print(f"    ✗ Requests returned too little content")
    except Exception as e:
        print(f"    ✗ Requests failed: {e}")
    
    # Attempt 3: Manual input
    print(f"    Method 3: Requesting manual input...")
    result = get_manual_content(url, campus)
    if result:
        return result
    
    # All methods failed
    print(f"    ✗ All scraping methods failed for {url}")
    return ""


async def scrape_all():
    """Scrape all URLs for all campuses and save results to JSON."""
    os.makedirs("data/raw", exist_ok=True)
    
    results = {}
    
    for campus, urls in URLS.items():
        print(f"\n{'='*60}")
        print(f"  CAMPUS: {campus.upper()}")
        print(f"{'='*60}")
        
        campus_pages = []
        
        for url in urls:
            print(f"\n  URL: {url}")
            
            # Random delay between pages (avoids rate limiting)
            if campus_pages or results:  # Not the very first request
                delay = random.uniform(3, 6)
                print(f"  Waiting {delay:.1f}s before next request...")
                await asyncio.sleep(delay)
            
            text = await scrape_page(url, campus)
            
            if text:
                campus_pages.append({
                    "url": url,
                    "campus": campus,
                    "content": text,
                    "char_count": len(text)
                })
                print(f"  ✓ Saved: {len(text):,} characters")
            else:
                print(f"  ✗ SKIPPED: No content retrieved for {url}")
        
        results[campus] = campus_pages
    
    # Save to file
    output_path = "data/raw/scraped_data.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\n{'='*60}")
    print(f"✅ SCRAPING COMPLETE → {output_path}")
    print(f"{'='*60}")
    for campus, pages in results.items():
        if pages:
            total = sum(p["char_count"] for p in pages)
            print(f"  {campus.upper()}: {len(pages)} pages, {total:,} chars")
        else:
            print(f"  {campus.upper()}: ⚠️  No content retrieved")


if __name__ == "__main__":
    asyncio.run(scrape_all())