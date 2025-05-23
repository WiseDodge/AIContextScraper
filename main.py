"""Main entry point for AIContextScraper."""

import asyncio
import os
from datetime import datetime, UTC
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
    exporter = ContentExporter(output_dir=output_dir, logger=logger)
    
    logger.info(f"Starting scrape of {url}")
    start_time = datetime.now(UTC)
    
    try:
        # Fetch pages
        async with AsyncFetcher(url, logger) as fetcher:
            crawl_results = await fetcher.crawl(url)
        
        total_pages = len(crawl_results['pages'])
        logger.info(f"Found {total_pages} pages to process")
        
        # Process each page
        total_tokens = 0
        total_errors = 0
        for page in crawl_results['pages']:
            try:
                # Validate page data
                if not page:
                    logger.warning("Skipping null page data")
                    continue

                page_url = page.get('url', 'unknown URL')
                logger.info(f"Processing page: {page_url}")

                # Try to get HTML content with fallback
                html_content = page.get('html', '')
                if not html_content or not html_content.strip():
                    logger.warning(f"No HTML content found for {page_url}")
                    continue

                # Parse content with enhanced error handling
                try:
                    parsed_data = parser.parse_page({
                        'html': html_content,
                        'url': page_url,
                        'title': page.get('title', '')
                    })
                    
                    chunks = parser.get_chunks(parsed_data['content'])
                    total_tokens += parsed_data.get('tokens', 0)
                    
                    # Export with fallback
                    try:
                        # Save text content first as fallback
                        await exporter.save_txt(page_url, parsed_data['content'])
                        # Then try full export
                        await exporter.export_page(parsed_data, chunks)
                    except Exception as export_error:
                        logger.error(f"Failed to export {page_url}: {str(export_error)}")
                        total_errors += 1
                    
                except Exception as parse_error:
                    logger.warning(f"Failed to parse {page_url}: {str(parse_error)}")
                    # Save raw content as fallback
                    await exporter.save_txt(page_url, html_content)
                    total_errors += 1
                    
            except Exception as e:
                logger.error(f"Error processing page {page_url}: {str(e)}")
                total_errors += 1
                continue

        # Final output logging
        if total_errors > 0:
            logger.warning(f"Scraping completed with {total_errors} errors. Check logs for details.")
        else:
            logger.info("Scraping completed successfully!")
        
        # Calculate statistics
        end_time = datetime.now(UTC)
        duration = (end_time - start_time).total_seconds()
        
        # Prepare run metadata
        metadata = {
            "source": url,
            "run_time": start_time.isoformat(timespec='seconds'),
            "duration_seconds": duration,
            "doc_count": total_pages,
            "total_tokens": total_tokens,
            "exported": ["json", "txt"] + (["pdf"] if PDF_ENABLED else []),
            "failed_urls": crawl_results['failed_urls']
        }
        
        # Save run metadata
        await exporter.save_metadata(metadata)
        
        logger.info(f"Scraping completed in {duration:.2f} seconds with {total_pages} pages processed")
        return metadata
    
    except Exception as e:
        logger.error(f"Scraping failed: {str(e)}", exc_info=True)
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