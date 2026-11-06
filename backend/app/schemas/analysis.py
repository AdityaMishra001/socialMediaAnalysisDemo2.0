from __future__ import annotations
from typing import List, Optional, Literal, Dict, Any
from pydantic import BaseModel, Field

class SentimentDistribution(BaseModel):
    positive: int = Field(ge=0, le=100, description="Percentage positive")
    negative: int = Field(ge=0, le=100, description="Percentage negative")
    neutral: int = Field(ge=0, le=100, description="Percentage neutral")
    mixed: int = Field(ge=0, le=100, description="Percentage mixed")

class EmotionBreakdown(BaseModel):
    frustration: int = Field(ge=0, le=100)
    delight: int = Field(ge=0, le=100)
    confusion: int = Field(ge=0, le=100)
    excitement: int = Field(ge=0, le=100)
    disappointment: int = Field(ge=0, le=100)
    satisfaction: int = Field(ge=0, le=100)

class ThemeItem(BaseModel):
    theme: str
    count: int = Field(ge=1)
    sentiment: Literal["positive", "negative", "neutral", "mixed"]
    urgency: Literal["low", "medium", "high", "critical"]
    representative_quotes: List[str] = Field(default_factory=list)

class AspectSentiment(BaseModel):
    aspect: str
    sentiment: Literal["positive", "negative", "neutral", "mixed"]
    score: float = Field(ge=0.0, le=1.0)
    supporting_examples: List[str] = Field(default_factory=list)

class Recommendation(BaseModel):
    title: str
    priority: Literal["high", "medium", "low"]
    rationale: str
    expected_impact: str
    effort: Literal["low", "medium", "high"]
    category: str

class AnalysisResult(BaseModel):
    overall_sentiment: Literal["positive", "negative", "neutral", "mixed"]
    sentiment_distribution: SentimentDistribution
    emotion_breakdown: EmotionBreakdown
    executive_summary: str
    key_themes: List[ThemeItem]
    aspect_sentiments: List[AspectSentiment]
    common_complaints: List[str]
    recurring_questions: List[str]
    suggestions: List[str]
    feature_requests: List[str]
    recommendations: List[Recommendation]
    total_items_analyzed: int
    confidence_score: float = 0.95
    is_simulated: bool = False

class AnalysisCreateRequest(BaseModel):
    feedback_text: Optional[str] = None
    feedback_source: str = "general"
    analysis_goal: str = "general"
    language: str = "auto"

class AnalysisResponse(BaseModel):
    id: str
    feedback_source: str
    analysis_goal: str
    language: str
    item_count: int
    raw_sample: Optional[str] = None
    status: str
    social_metadata: Optional[Dict[str, Any]] = None
    result: AnalysisResult
    error_message: Optional[str] = None
    created_at: Optional[str] = None
