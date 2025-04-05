"""Content exporter for various output formats."""

import json
import os
import asyncio
from typing import Dict, List, Any
from datetime import datetime
import aiofiles
import importlib

from config import OUTPUT_DIRS, PDF_ENABLED
from .logger import ScraperLogger

class ContentExporter:
    def __init__(self, output_dir: str, logger: ScraperLogger):
        self.output_dir = output_dir
        self.logger = logger
        self.txt_dir = os.path.join(self.output_dir, 'txt')
        os.makedirs(self.txt_dir, exist_ok=True)
        self.base_dir = self.output_dir

    def save_txt(self, url: str, content: str):
        """Save content as a text file in the /txt folder."""
        from urllib.parse import urlparse
        import os

        parsed = urlparse(url)
        filename = parsed.path.strip("/").replace("/", "_") or "index"
        if not filename.endswith(".txt"):
            filename += ".txt"
        path = os.path.join(self.txt_dir, filename)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        self.logger.info(f"Saved TXT for {url} at {path}")
    
    def _setup_directories(self) -> None:
        """Create output directory structure."""
        for dir_name in OUTPUT_DIRS:
            dir_path = os.path.join(self.base_dir, dir_name)
            os.makedirs(dir_path, exist_ok=True)
    
    def _sanitize_filename(self, filename: str) -> str:
        """Create a safe filename from URL or title."""
        # Remove or replace unsafe characters
        safe_name = ''.join(c if c.isalnum() or c in '.-_' else '_' for c in filename)
        return safe_name[:100]  # Limit length
    
    async def save_raw_html(self, url: str, html: str) -> None:
        """Save raw HTML content."""
        filename = self._sanitize_filename(url) + '.html'
        filepath = os.path.join(self.base_dir, 'raw_html', filename)
        
        async with aiofiles.open(filepath, 'w', encoding='utf-8') as f:
            await f.write(html)
    
    async def save_json(self, metadata: Dict[str, Any]) -> None:
        """Save structured content as JSON."""
        filename = self._sanitize_filename(metadata['url']) + '.json'
        filepath = os.path.join(self.base_dir, 'json', filename)
        
        async with aiofiles.open(filepath, 'w', encoding='utf-8') as f:
            await f.write(json.dumps(metadata, indent=2, ensure_ascii=False))
    
    async def save_txt_chunks(self, url: str, chunks: List[Dict[str, Any]]) -> None:
        """Save content chunks as TXT files."""
        base_filename = self._sanitize_filename(url)
        
        for i, chunk in enumerate(chunks, 1):
            filename = f"{base_filename}_chunk{i}.txt"
            filepath = os.path.join(self.base_dir, 'txt', filename)
            
            async with aiofiles.open(filepath, 'w', encoding='utf-8') as f:
                await f.write(chunk['content'])
    
    async def save_pdf(self, url: str, html: str) -> None:
        """Save content as PDF."""
        if not PDF_ENABLED:
            return
        
        filename = self._sanitize_filename(url) + '.pdf'
        filepath = os.path.join(self.base_dir, 'pdf', filename)
        
        try:
            # Dynamically import PDF libraries only when needed
            weasyprint = importlib.import_module('weasyprint')
            weasyprint.HTML(string=html).write_pdf(filepath)
        except Exception as e:
            self.logger.warning(f"WeasyPrint failed, falling back to pdfkit: {e}")
            try:
                # Dynamically import pdfkit
                pdfkit = importlib.import_module('pdfkit')
                pdfkit.from_string(html, filepath)
            except Exception as e:
                self.logger.error(f"PDF export failed: {e}")
    
    async def save_metadata(self, metadata: Dict[str, Any]) -> None:
        """Save run metadata including statistics."""
        filepath = os.path.join(self.base_dir, 'metadata.json')
        
        async with aiofiles.open(filepath, 'w', encoding='utf-8') as f:
            await f.write(json.dumps(metadata, indent=2, ensure_ascii=False))
    
    async def export_page(self, page_data: Dict[str, Any], chunks: List[Dict[str, Any]]) -> None:
        """Export a single page in all requested formats."""
        url = page_data['url']
        
        # Save all formats concurrently
        await asyncio.gather(
            self.save_raw_html(url, page_data['html']),
            self.save_json(page_data),
            self.save_txt_chunks(url, chunks)
        )
        
        if PDF_ENABLED:
            # PDF generation is synchronous, so we don't include it in gather
            await self.save_pdf(url, page_data['html'])