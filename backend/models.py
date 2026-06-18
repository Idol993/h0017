from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from database import Base


class Deck(Base):
    __tablename__ = "decks"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    language_pair = Column(String, default="zh-en")
    cover_color = Column(String, default="#3B82F6")

    cards = relationship("Card", back_populates="deck", cascade="all, delete-orphan")


class Card(Base):
    __tablename__ = "cards"

    id = Column(Integer, primary_key=True, index=True)
    deck_id = Column(Integer, ForeignKey("decks.id"), nullable=False)
    front = Column(String, nullable=False)
    back = Column(String, nullable=False)
    image_url = Column(String, nullable=True)
    tags = Column(JSON, default=list)
    last_reviewed = Column(DateTime, nullable=True)
    next_review = Column(DateTime, server_default=func.now())
    memory_strength = Column(Float, default=2.5)
    consecutive_correct = Column(Integer, default=0)
    interval_days = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())

    deck = relationship("Deck", back_populates="cards")
    review_logs = relationship("ReviewLog", back_populates="card", cascade="all, delete-orphan")


class ReviewLog(Base):
    __tablename__ = "review_logs"

    id = Column(Integer, primary_key=True, index=True)
    card_id = Column(Integer, ForeignKey("cards.id"), nullable=False)
    rating = Column(Integer, nullable=False)
    duration_seconds = Column(Integer, default=0)
    reviewed_at = Column(DateTime, server_default=func.now())

    card = relationship("Card", back_populates="review_logs")
