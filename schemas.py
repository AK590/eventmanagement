# schemas.py
from pydantic import BaseModel, EmailStr, validator
from typing import Optional, List
from datetime import datetime
import re

# --- Tier Schemas ---
class TierBase(BaseModel):
    name: str
    price: float
    total_seats: int

class TierCreate(TierBase):
    pass

class Tier(TierBase):
    id: int
    seats_sold: int
    class Config:
        from_attributes = True

# --- Sponsor Schemas ---
class SponsorBase(BaseModel):
    name: str
    website: Optional[str] = None
    logo_url: Optional[str] = None

class SponsorCreate(SponsorBase):
    pass

class Sponsor(SponsorBase):
    id: int
    class Config:
        from_attributes = True

# --- Event Schemas ---
class EventBase(BaseModel):
    title: str
    description: Optional[str] = None
    location: Optional[str] = None
    start_time: datetime
    end_time: datetime

class EventCreate(EventBase):
    tiers: List[TierCreate]
    sponsor_ids: List[int] = []

class Event(EventBase):
    id: int
    tiers: List[Tier] = []
    sponsors: List[Sponsor] = []
    class Config:
        from_attributes = True

class EventDetail(Event):
    total_collection: float

# --- Booking Schemas ---
class BookingBase(BaseModel):
    user_phone: str
    event_id: int
    tier_id: int
    qty: int

class BookingCreate(BookingBase):
    @validator('user_phone')
    def validate_phone_number(cls, v):
        if not re.match(r'^\d{10}$', v):
            raise ValueError('Phone number must be exactly 10 digits.')
        return v

class Booking(BookingBase):
    id: int
    price_paid: float
    ticket_hash: str
    class Config:
        from_attributes = True

class BookingDetail(BaseModel):
    ticket_hash: str
    qty: int
    user_phone: str
    tier_name: str

    class Config:
        from_attributes = True

# --- Other Schemas ---
class VerifiedBookingDetail(BaseModel):
    status: str
    event_title: str
    user_phone: str
    qty: int
    ticket_hash: str

class PriceRequest(BaseModel):
    tier_id: int
    qty: int

class PriceResponse(BaseModel):
    dynamic_price: float
    base_price: float
    quantity: int

class UserBase(BaseModel):
    email: EmailStr

class UserCreate(UserBase):
    name: str
    password: str
    phone: Optional[str] = None

class User(UserBase):
    id: int
    name: str
    phone: Optional[str] = None
    class Config:
        from_attributes = True

class ServiceBase(BaseModel):
    provider_name: str
    description: Optional[str] = None
    price: float
    contact: Optional[str] = None

class ServiceCreate(ServiceBase):
    pass

class Service(ServiceBase):
    id: int
    event_id: int
    class Config:
        from_attributes = True

