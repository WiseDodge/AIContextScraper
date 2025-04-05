"""HTML content parser and structurer for AIContextScraper."""

from typing import Dict, List, Any
from bs4 import BeautifulSoup
import re
import tiktoken
from datetime import datetime, UTC

from config import CHUNK_SIZE, METADATA_TEMPLATE

class ContentParser:
    def __init__(self):
        self.tokenizer = tiktoken.get_encoding("cl100k_base")
    
    def clean_text(self, text: str) -> str:
        """Clean and normalize text content."""
        # Remove extra whitespace and normalize line endings
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        # Remove special characters but keep basic punctuation
        text = re.sub(r'[^\w\s.,!?-]', '', text)
        
        return text
    
    def count_tokens(self, text: str) -> int:
        """Count the number of tokens in the text."""
        return len(self.tokenizer.encode(text))
    
    def chunk_content(self, content: str) -> List[str]:
        """Split content into chunks based on token count."""
        chunks = []
        current_chunk = []
        current_tokens = 0
        
        # Split into sentences first
        sentences = re.split(r'(?<=[.!?])\s+', content)
        
        for sentence in sentences:
            sentence_tokens = self.count_tokens(sentence)
            
            if current_tokens + sentence_tokens > CHUNK_SIZE:
                if current_chunk:
                    chunks.append(' '.join(current_chunk))
                current_chunk = [sentence]
                current_tokens = sentence_tokens
            else:
                current_chunk.append(sentence)
                current_tokens += sentence_tokens
        
        if current_chunk:
            chunks.append(' '.join(current_chunk))
        
        return chunks
    
    def extract_content(self, html: str) -> str:
        """Extract main content from HTML while preserving important structure."""
        soup = BeautifulSoup(html, 'lxml')
        
        # Remove unwanted elements
        for element in soup.find_all(['script', 'style', 'nav', 'footer', 'header']):
            element.decompose()
        
        # Extract text from remaining elements
        content = []
        for element in soup.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li']):
            text = element.get_text(strip=True)
            if text:
                # Add appropriate spacing based on element type
                if element.name.startswith('h'):
                    content.append(f"\n{text}\n")
                else:
                    content.append(text)
        
        return '\n'.join(content)
    
    def parse_page(self, page_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse a page and return structured content with metadata."""
        metadata = METADATA_TEMPLATE.copy()
        
        try:
            # Validate and extract HTML content
            if not isinstance(page_data, dict):
                raise TypeError(f"Page data must be a dictionary, got {type(page_data).__name__}")
            
            required_keys = {'html', 'url', 'title'}
            missing_keys = required_keys - page_data.keys()
            if missing_keys:
                raise ValueError(f"Missing required keys in page_data: {', '.join(missing_keys)}")
            
            if 'html' not in page_data:
                raise ValueError(f"Missing 'html' key in page_data. Keys found: {list(page_data.keys())}")
            
            html_content = page_data.get('html')
            if html_content is None:
                raise ValueError("HTML content is None")
            if not isinstance(html_content, str):
                raise ValueError(f"HTML content must be a string, got {type(html_content)}")
            if not html_content.strip():
                raise ValueError("HTML content is empty")
            
            # Process content
            raw_content = self.extract_content(html_content)
            if not raw_content.strip():
                raise ValueError("No content extracted from HTML")
                
            cleaned_content = self.clean_text(raw_content)
            
            # Update metadata with validated data
            metadata.update({
                'title': str(page_data.get('title', '')).strip(),
                'url': str(page_data.get('url', '')).strip(),
                'content': cleaned_content,
                'tokens': self.count_tokens(cleaned_content),
                'timestamp': datetime.now(UTC).isoformat(timespec='seconds')
            })
            
            return metadata
        except Exception as e:
            raise ValueError(f"Failed to parse page: {str(e)}") from e
    
    def get_chunks(self, content: str) -> List[Dict[str, Any]]:
        """Split content into chunks with metadata."""
        chunks = self.chunk_content(content)
        
        return [{
            'content': chunk,
            'tokens': self.count_tokens(chunk)
        } for chunk in chunks]


def clean_text_fallback(raw_text: str) -> str:
    """Quick and dirty fallback cleaner."""
    from html import unescape
    import re

    text = unescape(raw_text)
    text = re.sub(r'<[^>]+>', '', text)  # Remove HTML tags
    text = re.sub(r'\s+', ' ', text)     # Collapse whitespace
    return text.strip()