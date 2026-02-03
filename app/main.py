import asyncio
import os
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Form, BackgroundTasks, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv

from . import database
from .scraper.crawler import DocumentationCrawler
from .processor.cleaner import ContentCleaner
from .processor.chunker import DocumentChunker
from .ai.openai_client import OpenAIClient

load_dotenv()

# Get base directory
BASE_DIR = Path(__file__).resolve().parent.parent

@asynccontextmanager
async def lifespan(app: FastAPI):
    await database.init_db()
    yield

app = FastAPI(
    title="Doc Simplifier",
    description="Simplify any documentation for non-technical users",
    lifespan=lifespan
)

# Mount static files
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

# Templates
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Home page with URL input form."""
    recent_reports = await database.get_recent_reports(5)
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "recent_reports": recent_reports}
    )


@app.post("/simplify")
async def simplify(
    request: Request,
    background_tasks: BackgroundTasks,
    url: str = Form(...)
):
    """Submit a URL for simplification."""
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    report_id = await database.create_report(url)
    background_tasks.add_task(process_documentation, report_id, url)
    return RedirectResponse(url=f"/processing/{report_id}", status_code=303)


@app.get("/processing/{report_id}", response_class=HTMLResponse)
async def processing(request: Request, report_id: int):
    """Show processing progress page."""
    report = await database.get_report(report_id)

    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    if report["status"] == "complete":
        return RedirectResponse(url=f"/report/{report_id}", status_code=303)

    return templates.TemplateResponse(
        "processing.html",
        {"request": request, "report": report}
    )


@app.get("/api/status/{report_id}")
async def get_status(report_id: int):
    """API endpoint to check processing status."""
    report = await database.get_report(report_id)

    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    return {
        "status": report["status"],
        "progress": report["progress"],
        "progress_message": report["progress_message"],
        "error": report.get("error")
    }


@app.get("/report/{report_id}", response_class=HTMLResponse)
async def view_report(request: Request, report_id: int):
    """View completed report."""
    report = await database.get_report(report_id)

    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    if report["status"] == "processing":
        return RedirectResponse(url=f"/processing/{report_id}", status_code=303)

    return templates.TemplateResponse(
        "report.html",
        {"request": request, "report": report}
    )


@app.get("/history", response_class=HTMLResponse)
async def history(request: Request):
    """Show all reports."""
    reports = await database.get_all_reports()
    return templates.TemplateResponse(
        "history.html",
        {"request": request, "reports": reports}
    )


@app.delete("/report/{report_id}")
async def delete_report(report_id: int):
    """Delete a report."""
    deleted = await database.delete_report(report_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Report not found")
    return {"status": "deleted"}


async def process_documentation(report_id: int, url: str):
    """Background task to process documentation."""
    try:
        async def update_progress(progress: int, message: str):
            await database.update_report_progress(report_id, progress, message)

        # Step 1: Crawl
        await update_progress(5, "🔍 Crawling documentation...")
        crawler = DocumentationCrawler(max_depth=2, max_pages=20)
        pages = await crawler.crawl(url, progress_callback=update_progress)

        if not pages:
            await database.fail_report(report_id, "No content found at URL")
            return

        await update_progress(40, f"📄 Found {len(pages)} pages...")

        title = pages[0].get("title", "Documentation")
        await database.update_report_content(report_id, title, "")

        # Step 2: Clean
        cleaner = ContentCleaner()
        cleaned = cleaner.clean_content(pages)
        cleaned = cleaner.simplify_code_blocks(cleaned)

        await update_progress(45, "🧹 Content cleaned...")

        # Step 3: Chunk
        chunker = DocumentChunker(max_tokens=6000)
        chunks = chunker.chunk_document(cleaned)

        await update_progress(48, "🤖 AI is reading...")

        # Step 4: AI
        client = OpenAIClient()
        report_data = await client.generate_report(cleaned, chunks, update_progress)

        # Step 5: Done
        await update_progress(95, "✨ Finalizing...")
        await database.complete_report(report_id, report_data)

    except Exception as e:
        import traceback
        print(f"Error: {e}")
        traceback.print_exc()
        await database.fail_report(report_id, str(e)[:200])
