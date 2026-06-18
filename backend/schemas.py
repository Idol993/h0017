from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator


class DeckCreate(BaseModel):
    name: str
    language_pair: str = "zh-en"
    cover_color: str = "#3B82F6"


class DeckUpdate(BaseModel):
    name: Optional[str] = None
    language_pair: Optional[str] = None
    cover_color: Optional[str] = None


class DeckResponse(BaseModel):
    id: int
    name: str
    language_pair: str
    cover_color: str

    class Config:
        from_attributes = True


class CardCreate(BaseModel):
    deck_id: int
    front: str
    back: str
    image_url: Optional[str] = None
    tags: List[str] = []


class CardUpdate(BaseModel):
    deck_id: Optional[int] = None
    front: Optional[str] = None
    back: Optional[str] = None
    image_url: Optional[str] = None
    tags: Optional[List[str]] = None


class CardResponse(BaseModel):
    id: int
    deck_id: int
    front: str
    back: str
    image_url: Optional[str] = None
    tags: List[str] = []
    last_reviewed: Optional[datetime] = None
    next_review: datetime
    memory_strength: float
    consecutive_correct: int
    interval_days: int
    created_at: datetime

    @field_validator("tags", mode="before")
    @classmethod
    def fix_tags(cls, v):
        if v is None:
            return []
        return v

    class Config:
        from_attributes = True


class CardWithDeck(CardResponse):
    deck_name: str
    deck_color: str


class ReviewSubmit(BaseModel):
    rating: int = Field(..., ge=1, le=5)
    duration_seconds: int = 0


class ReviewSubmitBody(BaseModel):
    card_id: int
    rating: int = Field(..., ge=1, le=5)
    duration_seconds: int = 0


class TodayCard(CardWithDeck):
    is_overdue: bool
    overdue_days: int


class DeckStats(BaseModel):
    deck_id: int
    deck_name: str
    total_cards: int
    mastered_cards: int
    mastery_rate: float


class Stats(BaseModel):
    total_cards: int
    today_reviewed: int
    daily_reviews_last_30_days: Dict[str, int]
    deck_mastery_rates: List[DeckStats]
