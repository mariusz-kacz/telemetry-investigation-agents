from datetime import datetime
from typing import Protocol

from pydantic import BaseModel, Field


class Timestamped(Protocol):
    timestamp: datetime


class ParsedLogRecord(BaseModel):
    timestamp: datetime
    level: str = Field(min_length=1)
    service: str = Field(min_length=1)
    message: str = Field(min_length=1)
    correlation_id: str | None = None
    trace_id: str | None = None
    exception_type: str | None = None


class ParsedTraceSpan(BaseModel):
    timestamp: datetime
    trace_id: str = Field(min_length=1)
    span_id: str = Field(min_length=1)
    service: str = Field(min_length=1)
    operation: str = Field(min_length=1)
    duration_ms: int = Field(ge=0)
    status: str = Field(min_length=1)


class ParsedMetricSample(BaseModel):
    timestamp: datetime
    service: str = Field(min_length=1)
    metric_name: str = Field(min_length=1)
    value: float
