import csv
import io
import json
from datetime import datetime, timedelta
from typing import Optional, List
from collections import defaultdict

from fastapi import FastAPI, Depends, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from database import engine, get_db, Base
from models import Deck, Card, ReviewLog
from schemas import (
    DeckCreate, DeckResponse, DeckUpdate,
    CardCreate, CardResponse, CardUpdate, CardWithDeck,
    ReviewSubmit, TodayCard, Stats, DeckStats
)
from sm2 import calculate_next_interval

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Flashcards API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/decks", response_model=List[DeckResponse])
def list_decks(db: Session = Depends(get_db)):
    decks = db.query(Deck).all()
    return decks


@app.post("/api/decks", response_model=DeckResponse)
def create_deck(deck_data: DeckCreate, db: Session = Depends(get_db)):
    deck = Deck(**deck_data.model_dump())
    db.add(deck)
    db.commit()
    db.refresh(deck)
    return deck


@app.put("/api/decks/{deck_id}", response_model=DeckResponse)
def update_deck(deck_id: int, deck_data: DeckUpdate, db: Session = Depends(get_db)):
    deck = db.query(Deck).filter(Deck.id == deck_id).first()
    if not deck:
        raise HTTPException(status_code=404, detail="Deck not found")
    for key, value in deck_data.model_dump(exclude_unset=True).items():
        setattr(deck, key, value)
    db.commit()
    db.refresh(deck)
    return deck


@app.delete("/api/decks/{deck_id}")
def delete_deck(deck_id: int, db: Session = Depends(get_db)):
    deck = db.query(Deck).filter(Deck.id == deck_id).first()
    if not deck:
        raise HTTPException(status_code=404, detail="Deck not found")
    db.delete(deck)
    db.commit()
    return {"message": "Deck deleted successfully"}


@app.get("/api/cards", response_model=List[CardResponse])
def list_cards(deck_id: Optional[int] = None, db: Session = Depends(get_db)):
    query = db.query(Card)
    if deck_id is not None:
        query = query.filter(Card.deck_id == deck_id)
    return query.all()


@app.post("/api/cards", response_model=CardResponse)
def create_card(card_data: CardCreate, db: Session = Depends(get_db)):
    deck = db.query(Deck).filter(Deck.id == card_data.deck_id).first()
    if not deck:
        raise HTTPException(status_code=404, detail="Deck not found")
    card = Card(**card_data.model_dump())
    db.add(card)
    db.commit()
    db.refresh(card)
    return card


@app.put("/api/cards/{card_id}", response_model=CardResponse)
def update_card(card_id: int, card_data: CardUpdate, db: Session = Depends(get_db)):
    card = db.query(Card).filter(Card.id == card_id).first()
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")
    for key, value in card_data.model_dump(exclude_unset=True).items():
        setattr(card, key, value)
    db.commit()
    db.refresh(card)
    return card


@app.delete("/api/cards/{card_id}")
def delete_card(card_id: int, db: Session = Depends(get_db)):
    card = db.query(Card).filter(Card.id == card_id).first()
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")
    db.delete(card)
    db.commit()
    return {"message": "Card deleted successfully"}


@app.get("/api/today", response_model=List[TodayCard])
def get_today_cards(db: Session = Depends(get_db)):
    now = datetime.now()
    today_end = datetime(now.year, now.month, now.day) + timedelta(days=1)

    cards = db.query(Card).filter(Card.next_review <= today_end).all()

    result = []
    for card in cards:
        is_overdue = card.next_review < datetime(now.year, now.month, now.day)
        overdue_days = 0
        if is_overdue:
            overdue_days = (datetime(now.year, now.month, now.day) - card.next_review).days

        result.append(TodayCard(
            id=card.id,
            deck_id=card.deck_id,
            front=card.front,
            back=card.back,
            image_url=card.image_url,
            tags=card.tags or [],
            last_reviewed=card.last_reviewed,
            next_review=card.next_review,
            memory_strength=card.memory_strength,
            consecutive_correct=card.consecutive_correct,
            interval_days=card.interval_days,
            created_at=card.created_at,
            deck_name=card.deck.name,
            deck_color=card.deck.cover_color,
            is_overdue=is_overdue,
            overdue_days=overdue_days,
        ))

    result.sort(key=lambda x: (not x.is_overdue, -x.overdue_days, x.deck_id))

    return result


@app.post("/api/review/{card_id}", response_model=CardResponse)
def submit_review(card_id: int, review_data: ReviewSubmit, db: Session = Depends(get_db)):
    card = db.query(Card).filter(Card.id == card_id).first()
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")

    updates = calculate_next_interval(card, review_data.rating)

    for key, value in updates.items():
        setattr(card, key, value)

    log = ReviewLog(
        card_id=card.id,
        rating=review_data.rating,
        duration_seconds=review_data.duration_seconds,
        reviewed_at=datetime.now(),
    )
    db.add(log)
    db.commit()
    db.refresh(card)
    return card


@app.post("/api/import/csv")
async def import_csv(deck_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    deck = db.query(Deck).filter(Deck.id == deck_id).first()
    if not deck:
        raise HTTPException(status_code=404, detail="Deck not found")

    content = await file.read()
    text = content.decode("utf-8-sig")
    reader = csv.reader(io.StringIO(text))

    existing = set()
    for c in db.query(Card).filter(Card.deck_id == deck_id).all():
        existing.add((c.front.strip(), c.back.strip()))

    imported = 0
    skipped = 0

    for row in reader:
        if len(row) < 2:
            continue
        front = row[0].strip()
        back = row[1].strip()
        if not front or not back:
            skipped += 1
            continue

        key = (front, back)
        if key in existing:
            skipped += 1
            continue

        tags = []
        if len(row) >= 3 and row[2].strip():
            tags = [t.strip() for t in row[2].split(",") if t.strip()]

        card = Card(
            deck_id=deck_id,
            front=front,
            back=back,
            tags=tags,
        )
        db.add(card)
        existing.add(key)
        imported += 1

    db.commit()
    return {"imported": imported, "skipped": skipped}


@app.get("/api/stats", response_model=Stats)
def get_stats(db: Session = Depends(get_db)):
    total_cards = db.query(Card).count()

    now = datetime.now()
    today_start = datetime(now.year, now.month, now.day)
    today_end = today_start + timedelta(days=1)
    today_reviewed = db.query(ReviewLog).filter(
        ReviewLog.reviewed_at >= today_start,
        ReviewLog.reviewed_at < today_end
    ).count()

    daily_reviews = {}
    for i in range(30):
        day_start = today_start - timedelta(days=i)
        day_end = day_start + timedelta(days=1)
        count = db.query(ReviewLog).filter(
            ReviewLog.reviewed_at >= day_start,
            ReviewLog.reviewed_at < day_end
        ).count()
        daily_reviews[day_start.strftime("%Y-%m-%d")] = count

    deck_mastery_rates = []
    decks = db.query(Deck).all()
    for deck in decks:
        total = len(deck.cards)
        mastered = 0
        for card in deck.cards:
            if card.interval_days >= 7 or card.consecutive_correct >= 3:
                mastered += 1
        rate = round(mastered / total, 4) if total > 0 else 0.0
        deck_mastery_rates.append(DeckStats(
            deck_id=deck.id,
            deck_name=deck.name,
            total_cards=total,
            mastered_cards=mastered,
            mastery_rate=rate,
        ))

    return Stats(
        total_cards=total_cards,
        today_reviewed=today_reviewed,
        daily_reviews_last_30_days=daily_reviews,
        deck_mastery_rates=deck_mastery_rates,
    )


@app.get("/api/export/json")
def export_json(db: Session = Depends(get_db)):
    decks = db.query(Deck).all()
    cards = db.query(Card).all()
    logs = db.query(ReviewLog).all()

    export_data = {
        "decks": [
            {
                "id": d.id,
                "name": d.name,
                "language_pair": d.language_pair,
                "cover_color": d.cover_color,
            }
            for d in decks
        ],
        "cards": [
            {
                "id": c.id,
                "deck_id": c.deck_id,
                "front": c.front,
                "back": c.back,
                "image_url": c.image_url,
                "tags": c.tags,
                "last_reviewed": c.last_reviewed.isoformat() if c.last_reviewed else None,
                "next_review": c.next_review.isoformat() if c.next_review else None,
                "memory_strength": c.memory_strength,
                "consecutive_correct": c.consecutive_correct,
                "interval_days": c.interval_days,
                "created_at": c.created_at.isoformat() if c.created_at else None,
            }
            for c in cards
        ],
        "review_logs": [
            {
                "id": l.id,
                "card_id": l.card_id,
                "rating": l.rating,
                "duration_seconds": l.duration_seconds,
                "reviewed_at": l.reviewed_at.isoformat() if l.reviewed_at else None,
            }
            for l in logs
        ],
    }

    return export_data


@app.post("/api/import/json")
async def import_json(file: UploadFile = File(...), db: Session = Depends(get_db)):
    content = await file.read()
    data = json.loads(content)

    db.query(ReviewLog).delete()
    db.query(Card).delete()
    db.query(Deck).delete()
    db.commit()

    deck_id_map = {}
    for deck_data in data.get("decks", []):
        old_id = deck_data.pop("id")
        deck = Deck(**deck_data)
        db.add(deck)
        db.flush()
        deck_id_map[old_id] = deck.id

    card_id_map = {}
    for card_data in data.get("cards", []):
        old_id = card_data.pop("id")
        old_deck_id = card_data.get("deck_id")
        if old_deck_id in deck_id_map:
            card_data["deck_id"] = deck_id_map[old_deck_id]
        for field in ["last_reviewed", "next_review", "created_at"]:
            if card_data.get(field):
                card_data[field] = datetime.fromisoformat(card_data[field])
        card = Card(**card_data)
        db.add(card)
        db.flush()
        card_id_map[old_id] = card.id

    for log_data in data.get("review_logs", []):
        log_data.pop("id", None)
        old_card_id = log_data.get("card_id")
        if old_card_id in card_id_map:
            log_data["card_id"] = card_id_map[old_card_id]
        if log_data.get("reviewed_at"):
            log_data["reviewed_at"] = datetime.fromisoformat(log_data["reviewed_at"])
        log = ReviewLog(**log_data)
        db.add(log)

    db.commit()
    return {
        "decks_imported": len(deck_id_map),
        "cards_imported": len(card_id_map),
        "logs_imported": len(data.get("review_logs", [])),
    }
