"""Async web page fetcher with retry logic and rate limiting."""

import asyncio
from typing import Optional, Dict, Any
from urllib.parse import urljoin, urlparse
from datetime import datetime, timezone
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup

from config import HEADERS, MAX_RETRIES, TIMEOUT, MAX_CONCURRENCY, BLACKLIST_PATTERNS, INITIAL_WAIT
from .logger import ScraperLogger

class AsyncFetcher:
    def __init__(self, base_url: str, logger: ScraperLogger):
        self.base_url = base_url
        self.domain = urlparse(base_url).netloc
        self.logger = logger
        self.visited_urls = set()
        self.failed_urls = set()
        self.playwright = None
        self.browser = None
        self.semaphore = asyncio.Semaphore(MAX_CONCURRENCY)
    
    async def __aenter__(self):
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=True)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

    async def fetch_page(self, url: str, retry_count: int = 0) -> Optional[Dict[str, Any]]:
        """Fetch a single page with retry logic and JavaScript rendering."""
        if not self._is_valid_url(url) or url in self.visited_urls:
            return None
        
        self.visited_urls.add(url)
        
        try:
            async with self.semaphore:
                page = await self.browser.new_page()
                await page.set_extra_http_headers(HEADERS)
                
                # Enhanced page loading strategy
                await page.goto(url, wait_until='domcontentloaded')
                
                # Wait for initial page load
                await page.wait_for_load_state('domcontentloaded')
                
                # Get initial HTML content
                initial_html = await page.content()
                
                try:
                    # Try to wait for additional dynamic content
                    await page.wait_for_load_state('networkidle', timeout=10000)
                    await page.wait_for_load_state('load', timeout=10000)
                    await asyncio.sleep(INITIAL_WAIT)
                    
                    # Get the final rendered HTML
                    html = await page.content()
                    
                    # Validate HTML content structure
                    soup = BeautifulSoup(html, 'lxml')
                    if not soup.find(['body', 'main', 'article', 'div']):
                        self.logger.warning(f"Using initial HTML content for {url} as fallback")
                        html = initial_html
                except Exception as e:
                    self.logger.warning(f"Using initial HTML content for {url} due to: {str(e)}")
                    html = initial_html
                
                # Final parsing of the HTML content
                soup = BeautifulSoup(html, 'lxml')
                title = await page.title() or soup.title.string if soup.title else url
                
                await page.close()
                
                if not html or html.strip() == "":
                    raise ValueError("Empty HTML content received")
                
                return {
                    'url': url,
                    'html': html,
                    'title': title,
                    'timestamp': datetime.now(timezone.utc).isoformat(timespec='seconds')
                }
                
        except Exception as e:
            self.logger.error(f"Error fetching {url}", e)
            if retry_count < MAX_RETRIES:
                await asyncio.sleep(2 ** retry_count)  # Exponential backoff
                return await self.fetch_page(url, retry_count + 1)
            
            self.failed_urls.add(url)
            
        return None

    def _is_valid_url(self, url: str) -> bool:
        """Check if URL should be crawled based on domain and blacklist patterns."""
        if not url or any(pattern in url for pattern in BLACKLIST_PATTERNS):
            return False
        
        parsed = urlparse(url)
        return parsed.netloc == self.domain
    
    def extract_links(self, html: str, current_url: str) -> set[str]:
        """Extract valid links from HTML content."""
        
        links = set()
        soup = BeautifulSoup(html, 'lxml')
        for anchor in soup.find_all('a', href=True):
            href = anchor['href']
            absolute_url = urljoin(current_url, href)
            
            if self._is_valid_url(absolute_url):
                links.add(absolute_url)
        
        return links
    
    async def crawl(self, start_url: str) -> Dict[str, Any]:
        """Recursively crawl pages starting from the given URL."""
        result = await self.fetch_page(start_url)
        if not result:
            return {'pages': [], 'failed_urls': list(self.failed_urls)}
        
        pages = [result]
        links = self.extract_links(result['html'], start_url)
        
        # Create tasks for all extracted links
        tasks = [self.fetch_page(link) for link in links]
        results = await asyncio.gather(*tasks)
        
        # Filter out None results and add successful fetches to pages
        pages.extend([r for r in results if r is not None])
        
        return {
            'pages': pages,
            'failed_urls': list(self.failed_urls)
        }