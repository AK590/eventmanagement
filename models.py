# models.py
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, Boolean, Text, Table
from sqlalchemy.orm import relationship
from .database import Base
import datetime

# Association table for the many-to-many relationship between events and sponsors
event_sponsor_association = Table('event_sponsor', Base.metadata,
    Column('event_id', Integer, ForeignKey('events.id')),
    Column('sponsor_id', Integer, ForeignKey('sponsors.id'))
)

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200))
    email = Column(String(200), unique=True, index=True)
    hashed_password = Column(String(200))
    phone = Column(String(50), unique=True, index=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    bookings = relationship("Booking", back_populates="user")

class Event(Base):
    __tablename__ = "events"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), index=True)
    description = Column(Text)
    location = Column(String(255))
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    tiers = relationship("Tier", back_populates="event", cascade="all, delete-orphan")
    services = relationship("Service", back_populates="event", cascade="all, delete-orphan")
    bookings = relationship("Booking", back_populates="event", cascade="all, delete-orphan")
    sponsors = relationship("Sponsor", secondary=event_sponsor_association, back_populates="events")

class Tier(Base):
    __tablename__ = "tiers"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    price = Column(Float, nullable=False)
    total_seats = Column(Integer, nullable=False)
    seats_sold = Column(Integer, default=0)
    event_id = Column(Integer, ForeignKey("events.id"))
    event = relationship("Event", back_populates="tiers")
    bookings = relationship("Booking", back_populates="tier")

class Service(Base):
    __tablename__ = "services"
    id = Column(Integer, primary_key=True, index=True)
    provider_name = Column(String(200), index=True)
    description = Column(Text)
    price = Column(Float)
    event_id = Column(Integer, ForeignKey("events.id"))
    contact = Column(String(200))
    event = relationship("Event", back_populates="services")

class Sponsor(Base):
    __tablename__ = "sponsors"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), index=True, unique=True)
    website = Column(String(255))
    logo_url = Column(String(255), nullable=True)
    events = relationship("Event", secondary=event_sponsor_association, back_populates="sponsors")

class Booking(Base):
    __tablename__ = "bookings"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    event_id = Column(Integer, ForeignKey("events.id"))
    tier_id = Column(Integer, ForeignKey("tiers.id"))
    qty = Column(Integer, default=1)
    price_paid = Column(Float)
    ticket_hash = Column(String(128), unique=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    verified = Column(Boolean, default=False)
    user = relationship("User", back_populates="bookings")
    event = relationship("Event", back_populates="bookings")
    tier = relationship("Tier", back_populates="bookings")

