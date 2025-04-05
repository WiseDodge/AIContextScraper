"""Configuration settings for the AIContextScraper."""

# HTTP request settings
HEADERS = {
    "User-Agent": "AIContextScraper/1.0"
}

# Crawler settings
MAX_CONCURRENCY = 10
MAX_RETRIES = 3
TIMEOUT = 10  # seconds

# Content processing settings
CHUNK_SIZE = 500  # max tokens or words per .txt split

# URL patterns to skip during crawling
BLACKLIST_PATTERNS = ["#top", ".jpg", ".png", ".gif", ".css", ".js"]

# Output directory structure
OUTPUT_DIRS = [
    "raw_html",
    "json",
    "txt",
    "pdf"
]

# Export settings
PDF_ENABLED = False  # Will be set via CLI input

# Metadata template for each page
METADATA_TEMPLATE = {
    "title": "",
    "url": "",
    "content": "",
    "tokens": 0,
    "timestamp": ""
}