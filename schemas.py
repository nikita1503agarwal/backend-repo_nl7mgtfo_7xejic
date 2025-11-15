"""
Database Schemas

App domain: Events and ticket bookings for concerts, cinema, dine-in reservations, and live shows.

Each Pydantic model represents a collection in MongoDB. Collection name is the lowercase class name.
"""
from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from datetime import datetime


class Venue(BaseModel):
    name: str = Field(..., description="Venue name")
    address: str = Field(..., description="Street address")
    city: str = Field(..., description="City name")
    state: Optional[str] = Field(None, description="State/Region")
    country: str = Field("USA", description="Country")
    capacity: Optional[int] = Field(None, ge=1, description="Seating capacity")


class Event(BaseModel):
    title: str = Field(..., description="Event title")
    category: str = Field(..., description="Category: concert | cinema | dine-in | live-show")
    description: Optional[str] = Field(None, description="Short description")
    date: datetime = Field(..., description="Event date/time in ISO format")
    duration_minutes: Optional[int] = Field(None, ge=0, description="Event duration in minutes")
    price: float = Field(..., ge=0, description="Base ticket price")
    currency: str = Field("USD", description="Currency code")
    venue: Venue = Field(..., description="Venue details")
    image_url: Optional[str] = Field(None, description="Hero image for the event")
    tags: List[str] = Field(default_factory=list, description="Searchable tags")
    available: bool = Field(True, description="Whether tickets are currently available")


class Booking(BaseModel):
    event_id: str = Field(..., description="Mongo _id of the event as string")
    name: str = Field(..., description="Full name of the customer")
    email: EmailStr = Field(..., description="Customer email")
    quantity: int = Field(..., ge=1, le=12, description="Number of tickets")
    notes: Optional[str] = Field(None, description="Special requests")

