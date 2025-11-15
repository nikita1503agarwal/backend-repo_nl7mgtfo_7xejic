import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from bson import ObjectId
from datetime import datetime

from database import db, create_document, get_documents
from schemas import Event, Booking

app = FastAPI(title="Event Booking API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    return {"message": "Event Booking Backend is running"}


@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": "❌ Not Set",
        "database_name": "❌ Not Set",
        "connection_status": "Not Connected",
        "collections": []
    }

    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Set"
            response["database_name"] = getattr(db, 'name', 'unknown')
            try:
                collections = db.list_collection_names()
                response["collections"] = collections
                response["database"] = "✅ Connected & Working"
                response["connection_status"] = "Connected"
            except Exception as e:
                response["database"] = f"⚠️ Connected but Error: {str(e)[:80]}"
        else:
            response["database"] = "⚠️ Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:80]}"

    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"

    return response


# Seed some demo events if none exist
@app.post("/api/seed")
def seed_events():
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")

    count = db["event"].count_documents({})
    if count > 0:
        return {"seeded": False, "message": "Events already exist"}

    demo_events = [
        {
            "title": "Neon Nights Live DJ",
            "category": "concert",
            "description": "An immersive EDM experience with holographic visuals.",
            "date": datetime.utcnow(),
            "duration_minutes": 180,
            "price": 59.0,
            "currency": "USD",
            "venue": {
                "name": "Pulse Arena",
                "address": "123 Bassline Ave",
                "city": "Los Angeles",
                "state": "CA",
                "country": "USA",
                "capacity": 12000
            },
            "image_url": "https://images.unsplash.com/photo-1540039155733-5bb30b53aa14?q=80&w=1600&auto=format&fit=crop",
            "tags": ["edm", "live", "neon"],
            "available": True
        },
        {
            "title": "Cinematic Premiere: Quantum Drift",
            "category": "cinema",
            "description": "Futuristic sci-fi premiere with cast Q&A.",
            "date": datetime.utcnow(),
            "duration_minutes": 140,
            "price": 18.0,
            "currency": "USD",
            "venue": {
                "name": "HoloCine 8",
                "address": "88 Spectrum Blvd",
                "city": "San Francisco",
                "state": "CA",
                "country": "USA",
                "capacity": 800
            },
            "image_url": "https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?q=80&w=1600&auto=format&fit=crop",
            "tags": ["cinema", "premiere"],
            "available": True
        },
        {
            "title": "Gastronoir: Tasting Menu",
            "category": "dine-in",
            "description": "Multi-course tasting with ambient synthwave.",
            "date": datetime.utcnow(),
            "duration_minutes": 120,
            "price": 95.0,
            "currency": "USD",
            "venue": {
                "name": "Obsidian Table",
                "address": "7 Eclipse Rd",
                "city": "New York",
                "state": "NY",
                "country": "USA",
                "capacity": 120
            },
            "image_url": "https://images.unsplash.com/photo-1467003909585-2f8a72700288?q=80&w=1600&auto=format&fit=crop",
            "tags": ["dining", "tasting"],
            "available": True
        }
    ]

    for e in demo_events:
        db["event"].insert_one({**e, "created_at": datetime.utcnow(), "updated_at": datetime.utcnow()})

    return {"seeded": True, "inserted": len(demo_events)}


@app.get("/api/events", response_model=List[Event])
def list_events(category: Optional[str] = None, q: Optional[str] = None):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")

    filt = {}
    if category:
        filt["category"] = category
    if q:
        filt["$or"] = [
            {"title": {"$regex": q, "$options": "i"}},
            {"description": {"$regex": q, "$options": "i"}},
            {"tags": {"$regex": q, "$options": "i"}},
        ]

    docs = get_documents("event", filt)

    # Convert Mongo docs to Event models - letting Pydantic coerce types
    result = []
    for d in docs:
        d.pop("_id", None)
        result.append(Event(**d))
    return result


@app.post("/api/book")
def create_booking(booking: Booking):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")

    # Validate event exists
    try:
        ev = db["event"].find_one({"_id": ObjectId(booking.event_id)})
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid event id")

    if not ev:
        raise HTTPException(status_code=404, detail="Event not found")

    bid = create_document("booking", booking)
    return {"ok": True, "booking_id": bid}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
