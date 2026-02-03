"""Database module - uses in-memory storage for serverless compatibility."""
import json
import os
from datetime import datetime
from typing import Optional
import asyncio

# In-memory storage (for serverless - consider using Vercel KV or Upstash Redis for persistence)
_reports = {}
_counter = 0
_lock = asyncio.Lock()


async def init_db():
    """Initialize database - no-op for in-memory."""
    pass


async def create_report(url: str) -> int:
    """Create a new report entry and return its ID."""
    global _counter
    async with _lock:
        _counter += 1
        report_id = _counter
        _reports[report_id] = {
            "id": report_id,
            "url": url,
            "title": None,
            "status": "processing",
            "progress": 0,
            "progress_message": "Starting...",
            "content": "",
            "report_data": None,
            "error": None,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "completed_at": None
        }
        return report_id


async def update_report_progress(report_id: int, progress: int, message: str):
    """Update report processing progress."""
    if report_id in _reports:
        _reports[report_id]["progress"] = progress
        _reports[report_id]["progress_message"] = message


async def update_report_content(report_id: int, title: str, content: str):
    """Update report with scraped content."""
    if report_id in _reports:
        _reports[report_id]["title"] = title
        _reports[report_id]["content"] = content


async def complete_report(report_id: int, report_data: dict):
    """Mark report as complete with final data."""
    if report_id in _reports:
        _reports[report_id]["status"] = "complete"
        _reports[report_id]["report_data"] = report_data
        _reports[report_id]["progress"] = 100
        _reports[report_id]["progress_message"] = "Complete!"
        _reports[report_id]["completed_at"] = datetime.now().strftime("%Y-%m-%d %H:%M")


async def fail_report(report_id: int, error: str):
    """Mark report as failed with error message."""
    if report_id in _reports:
        _reports[report_id]["status"] = "failed"
        _reports[report_id]["error"] = error


async def get_report(report_id: int) -> Optional[dict]:
    """Get a single report by ID."""
    return _reports.get(report_id)


async def get_recent_reports(limit: int = 5) -> list:
    """Get recent reports for homepage."""
    reports = sorted(_reports.values(), key=lambda x: x["id"], reverse=True)
    return reports[:limit]


async def get_all_reports() -> list:
    """Get all reports for history page."""
    return sorted(_reports.values(), key=lambda x: x["id"], reverse=True)


async def delete_report(report_id: int) -> bool:
    """Delete a report by ID."""
    if report_id in _reports:
        del _reports[report_id]
        return True
    return False
