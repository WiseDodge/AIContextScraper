"""FastAPI server for AIContextScraper web interface."""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import asyncio
import os
from typing import Optional

from main import scrape_site
from config import PDF_ENABLED

app = FastAPI(title="AIContextScraper API")

# CORS setup for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ScrapeRequest(BaseModel):
    url: str
    project_name: Optional[str] = None
    pdf_export: bool = False

@app.post("/api/scrape")
async def scrape_docs(req: ScrapeRequest):
    try:
        # Set PDF export preference
        global PDF_ENABLED
        PDF_ENABLED = req.pdf_export
        
        # Generate output directory
        domain = req.url.split('/')[2].split('.')[0]
        project_name = req.project_name or domain
        output_dir = os.path.join('D:', 'AI_Training_Corpora', project_name)
        os.makedirs(output_dir, exist_ok=True)
        
        # Run scraper
        metadata = await scrape_site(req.url, output_dir)
        
        return JSONResponse({
            "status": "success",
            "data": {
                "pages_processed": metadata['doc_count'],
                "total_tokens": metadata['total_tokens'],
                "duration_seconds": metadata['duration_seconds'],
                "output_directory": output_dir,
                "failed_urls": metadata['failed_urls']
            }
        })
        
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": str(e)
            }
        )

# Mount static files for web interface
app.mount("/", StaticFiles(directory="static", html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=3000)