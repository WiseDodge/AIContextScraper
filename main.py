"""Main entry point for AIContextScraper."""

import asyncio
import os
from datetime import datetime
from typing import Dict, Any
from urllib.parse import urlparse

from utils.fetcher import AsyncFetcher
from utils.parser import ContentParser
from utils.exporter import ContentExporter
from utils.logger import ScraperLogger
from config import PDF_ENABLED

async def scrape_site(url: str, output_dir: str) -> Dict[str, Any]:
    """Main scraping function that orchestrates the entire process."""
    # Initialize components
    logger = ScraperLogger(output_dir)
    parser = ContentParser()
    exporter = ContentExporter(output_dir, logger)
    
    logger.info(f"Starting scrape of {url}")
    start_time = datetime.utcnow()
    
    try:
        # Fetch pages
        async with AsyncFetcher(url, logger) as fetcher:
            crawl_results = await fetcher.crawl(url)
        
        total_pages = len(crawl_results['pages'])
        logger.info(f"Found {total_pages} pages to process")
        
        # Process each page
        total_tokens = 0
        for page in crawl_results['pages']:
            # Parse content
            parsed_data = parser.parse_page(page)
            chunks = parser.get_chunks(parsed_data['content'])
            total_tokens += parsed_data['tokens']
            
            # Export in all formats
            await exporter.export_page(parsed_data, chunks)
        
        # Calculate statistics
        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()
        
        # Prepare run metadata
        metadata = {
            "source": url,
            "run_time": start_time.isoformat() + 'Z',
            "duration_seconds": duration,
            "doc_count": total_pages,
            "total_tokens": total_tokens,
            "exported": ["json", "txt"] + (["pdf"] if PDF_ENABLED else []),
            "failed_urls": crawl_results['failed_urls']
        }
        
        # Save run metadata
        await exporter.save_metadata(metadata)
        
        logger.info(f"Scraping completed in {duration:.2f} seconds")
        return metadata
    
    except Exception as e:
        logger.error("Scraping failed", e)
        raise

def get_output_dir(url: str) -> str:
    """Generate output directory name from URL or prompt user."""
    # Extract domain name as default project name
    domain = urlparse(url).netloc.split('.')[0]
    project_name = input(f"Enter project name (default: {domain}): ").strip()
    
    if not project_name:
        project_name = domain
    
    # Create directory in standard location
    output_dir = os.path.join('D:', 'AI_Training_Corpora', project_name)
    os.makedirs(output_dir, exist_ok=True)
    
    return output_dir

def main():
    # Get input URL
    url = input("Enter the documentation website URL to scrape: ").strip()
    if not url:
        print("URL is required!")
        return
    
    # Get output location
    output_dir = get_output_dir(url)
    
    # Ask about PDF export
    pdf_export = input("Do you want to export PDF as well? (y/N): ").lower().strip() == 'y'
    global PDF_ENABLED
    PDF_ENABLED = pdf_export
    
    # Run the scraper
    try:
        metadata = asyncio.run(scrape_site(url, output_dir))
        
        # Print summary
        print("\nScraping completed successfully!")
        print(f"Pages processed: {metadata['doc_count']}")
        print(f"Total tokens: {metadata['total_tokens']}")
        print(f"Duration: {metadata['duration_seconds']:.2f} seconds")
        print(f"Output directory: {output_dir}")
        
        if metadata['failed_urls']:
            print(f"\nFailed URLs: {len(metadata['failed_urls'])}")
            for url in metadata['failed_urls']:
                print(f"  - {url}")
    
    except Exception as e:
        print(f"\nError: {str(e)}")
        return 1
    
    return 0

if __name__ == '__main__':
    exit(main())