from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class CodeAnalysisRequest(BaseModel):
    file_path: Optional[str] = None
    code: str
    language: Optional[str] = None


class Issue(BaseModel):
    type: str
    message: str
    line: Optional[int] = None
    severity: Optional[str] = "info"


class StructureInfo(BaseModel):
    functions: List[str] = []
    classes: List[str] = []


class CodeAnalysisResponse(BaseModel):
    file_path: Optional[str] = None
    language: Optional[str] = None
    issues: List[Issue] = []
    complexity: Optional[float] = None
    security_findings: List[Issue] = []
    structure: Optional[StructureInfo] = None
    summary: Optional[str] = None


class UnifiedAnalysisResponse(BaseModel):
    big_o: str
    cyclomatic_complexity: int
    maintainability: float
    security_summary: str
    ai_summary: str
    risk_level: str
    risk_score: int
    complexity_trend: str
    language_detected: Optional[str] = None
    detection_confidence: Optional[float] = None
    was_corrected: bool = False
    original_valid: bool = True
    corrected_code: Optional[str] = None

    # Optional Gemini-refined analysis (Python-first).
    algorithm: Optional[str] = None
    time_complexity: Optional[str] = None
    space_complexity: Optional[str] = None
    recommendation: Optional[str] = None
    explanation: Optional[str] = None

    error: Optional[str] = None
    message: Optional[str] = None


class CodeCompareRequest(BaseModel):
    original_code: str
    modified_code: str
    language: Optional[str] = None


class CodeDiff(BaseModel):
    added: List[str]
    removed: List[str]
    changed: List[str]


class CodeCompareResponse(BaseModel):
    diff: CodeDiff
    risk_score: Optional[float] = None
    summary: Optional[str] = None
    metrics_comparison: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    message: Optional[str] = None


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    context_snippet: Optional[str] = None


class ChatResponse(BaseModel):
    messages: List[ChatMessage]


class AutofixRequest(BaseModel):
    code: str


class AutofixChange(BaseModel):
    title: str
    description: str


class AutofixResponse(BaseModel):
    fixed_code: str
    diff_summary: List[str] = []
    changes: List[AutofixChange] = []


class ExtractCodeResponse(BaseModel):
    formatted_code: str
    filename: Optional[str] = None
    note: Optional[str] = None

