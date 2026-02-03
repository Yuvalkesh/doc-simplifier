from pydantic import BaseModel, HttpUrl
from typing import Optional, List
from datetime import datetime
from enum import Enum


class ProcessingStatus(str, Enum):
    PROCESSING = "processing"
    COMPLETE = "complete"
    FAILED = "failed"


class ReportSection(BaseModel):
    title: str
    icon: str
    content: str


class SimplifyRequest(BaseModel):
    url: str


class Report(BaseModel):
    id: int
    url: str
    title: Optional[str] = None
    status: ProcessingStatus = ProcessingStatus.PROCESSING
    progress: int = 0
    progress_message: str = "Starting..."
    sections: Optional[List[ReportSection]] = None
    error: Optional[str] = None
    created_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class ReportData(BaseModel):
    """Structure of the AI-generated report."""
    what_is_this: str
    who_is_this_for: str
    key_features: str
    use_cases: str
    getting_started: str
    common_operations: str
    pricing_limits: str
    alternatives: str


class CrawledPage(BaseModel):
    """A single crawled page."""
    url: str
    title: str
    content: str
    depth: int


class ProcessingProgress(BaseModel):
    """Progress update for frontend."""
    report_id: int
    progress: int
    message: str
    status: ProcessingStatus
