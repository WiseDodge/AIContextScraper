"""Async web page fetcher with retry logic and rate limiting."""

import asyncio
from typing import Optional, Dict, Any
import aiohttp
from urllib.parse import urljoin, urlparse
from datetime import datetime
import sys
from bs4 import BeautifulSoup

from ..config import HEADERS, MAX_RETRIES, TIMEOUT, MAX_CONCURRENCY, BLACKLIST_PATTERNS
from .logger import ScraperLogger

class AsyncFetcher:
    def __init__(self, base_url: str, logger: ScraperLogger):
        self.base_url = base_url
        self.domain = urlparse(base_url).netloc
        self.logger = logger
        self.session: Optional[aiohttp.ClientSession] = None
        self.semaphore = asyncio.Semaphore(MAX_CONCURRENCY)
        self.visited_urls = set()
        self.failed_urls = set()
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(headers=HEADERS)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def _is_valid_url(self, url: str) -> bool:
        """Check if URL should be crawled based on domain and blacklist patterns."""
        if not url or any(pattern in url for pattern in BLACKLIST_PATTERNS):
            return False
        
        parsed = urlparse(url)
        return parsed.netloc == self.domain
    
    async def fetch_page(self, url: str, retry_count: int = 0) -> Optional[Dict[str, Any]]:
        """Fetch a single page with retry logic."""
        if not self._is_valid_url(url) or url in self.visited_urls:
            return None
        
        self.visited_urls.add(url)
        
        try:
            async with self.semaphore:
                if not self.session:
                    raise RuntimeError("Session not initialized")
                
                async with self.session.get(url, timeout=TIMEOUT) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'lxml')
                        
                        return {
                            'url': url,
                            'html': html,
                            'title': soup.title.string if soup.title else url,
                            'timestamp': datetime.utcnow().isoformat() + 'Z'
                        }
                    else:
                        self.logger.warning(f"Failed to fetch {url}: Status {response.status}")
        
        except asyncio.TimeoutError:
            self.logger.warning(f"Timeout while fetching {url}")
        except Exception as e:
            self.logger.error(f"Error fetching {url}", e)
        
        if retry_count < MAX_RETRIES:
            await asyncio.sleep(2 ** retry_count)  # Exponential backoff
            return await self.fetch_page(url, retry_count + 1)
        
        self.failed_urls.add(url)
        return None
    
    def extract_links(self, html: str, current_url: str) -> set[str]:
        """Extract valid links from HTML content."""
        soup = BeautifulSoup(html, 'lxml')
        links = set()
        
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