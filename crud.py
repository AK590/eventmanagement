from sqlalchemy.orm import Session, joinedload, subqueryload
from sqlalchemy import func
from datetime import datetime
from passlib.context import CryptContext

# Corrected relative imports
from . import models, schemas
from .utils import gen_ticket_hash
from .ml_pricing import load_model, predict_price
from .blockchain import SimpleChain

model = load_model()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_or_create_user_by_phone(db: Session, phone: str):
    user = db.query(models.User).filter(models.User.phone == phone).first()
    if user:
        return user
    new_user = models.User(name=f"User {phone}", phone=phone)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

def create_event(db: Session, ev: schemas.EventCreate):
    event_data = ev.dict(exclude={"tiers", "sponsor_ids"})
    new_event = models.Event(**event_data)
    
    for tier_data in ev.tiers:
        new_tier = models.Tier(**tier_data.dict(), event=new_event)
        db.add(new_tier)

    if ev.sponsor_ids:
        sponsors = db.query(models.Sponsor).filter(models.Sponsor.id.in_(ev.sponsor_ids)).all()
        new_event.sponsors.extend(sponsors)

    db.add(new_event)
    db.commit()
    db.refresh(new_event)
    return new_event

def list_events(db: Session, skip=0, limit=50):
    events = db.query(models.Event).options(
        subqueryload(models.Event.tiers),
        subqueryload(models.Event.sponsors)
    ).offset(skip).limit(limit).all()
    
    event_details = []
    for event in events:
        total_collection = db.query(func.sum(models.Booking.price_paid)).filter(models.Booking.event_id == event.id).scalar() or 0.0
        average_rating = db.query(func.avg(models.Rating.rating)).filter(models.Rating.event_id == event.id).scalar()
        event_detail = schemas.EventDetail(
            **event.__dict__,
            total_collection=total_collection,
            average_rating=average_rating
        )
        event_details.append(event_detail)
    return event_details

def delete_event(db: Session, event_id: int):
    event = db.query(models.Event).filter(models.Event.id == event_id).first()
    if not event:
        return None
    db.delete(event)
    db.commit()
    return event

def compute_dynamic_price(tier: models.Tier, qty: int):
    event = tier.event
    total_tickets_sold_in_event = sum(t.seats_sold for t in event.tiers)
    hours_to_event = max((event.start_time - datetime.utcnow()).total_seconds() / 3600.0, 0.1)
    base_price = tier.price
    
    predicted_price_per_ticket = predict_price(model, total_tickets_sold_in_event + qty, hours_to_event, base_price)
    
    min_price = base_price 
    max_price = base_price * 1.5
    capped_price = max(min_price, min(predicted_price_per_ticket, max_price))
    
    return capped_price * qty

def get_dynamic_price(db: Session, price_request: schemas.PriceRequest):
    tier = db.query(models.Tier).filter(models.Tier.id == price_request.tier_id).first()
    if not tier:
        raise ValueError("Tier not found")
    
    price = compute_dynamic_price(tier, price_request.qty)
    
    return schemas.PriceResponse(
        dynamic_price=price,
        base_price=tier.price * price_request.qty,
        quantity=price_request.qty
    )

def book_ticket(db: Session, b: schemas.BookingCreate):
    user_obj = get_or_create_user_by_phone(db, phone=b.user_phone)
    
    tier = db.query(models.Tier).options(joinedload(models.Tier.event)).filter(models.Tier.id == b.tier_id).first()
    if not tier:
        raise ValueError("Tier not found")
    
    event = tier.event
    if tier.seats_sold + b.qty > tier.total_seats:
        raise ValueError("Not enough tickets available in this tier")
        
    timestamp = datetime.utcnow().isoformat()
    ticket_hash = gen_ticket_hash(user_obj.phone, event.id, timestamp)
    
    price = compute_dynamic_price(tier, b.qty)
    
    booking = models.Booking(
        user_id=user_obj.id, 
        event_id=event.id,
        tier_id=tier.id,
        qty=b.qty, 
        price_paid=price, 
        ticket_hash=ticket_hash
    )
    db.add(booking)
    tier.seats_sold += b.qty

    new_price_per_ticket = price / b.qty
    tier.price = new_price_per_ticket
    
    db.commit()
    db.refresh(booking)

    chain = SimpleChain(event_id=event.id)
    chain.add_block({"ticket_hash": ticket_hash, "user_phone": user_obj.phone, "event_id": event.id, "tier": tier.name})
    
    return schemas.Booking(
        id=booking.id,
        user_phone=user_obj.phone,
        event_id=booking.event_id,
        tier_id=booking.tier_id,
        qty=booking.qty,
        price_paid=booking.price_paid,
        ticket_hash=booking.ticket_hash
    )

def get_bookings_for_event(db: Session, event_id: int):
    bookings = db.query(models.Booking).options(
        joinedload(models.Booking.user),
        joinedload(models.Booking.tier)
    ).filter(models.Booking.event_id == event_id).all()
    
    booking_details = []
    for b in bookings:
        booking_details.append(
            schemas.BookingDetail(
                ticket_hash=b.ticket_hash,
                qty=b.qty,
                user_phone=b.user.phone,
                tier_name=b.tier.name
            )
        )
    return booking_details

def verify_ticket(db: Session, ticket_hash: str):
    booking = db.query(models.Booking).options(
        joinedload(models.Booking.user),
        joinedload(models.Booking.event)
    ).filter(models.Booking.ticket_hash == ticket_hash).first()

    if not booking:
        return None

    return schemas.VerifiedBookingDetail(
        status="Ticket Verified Successfully",
        event_title=booking.event.title,
        user_phone=booking.user.phone,
        qty=booking.qty,
        ticket_hash=booking.ticket_hash
    )

def create_sponsor(db: Session, sponsor: schemas.SponsorCreate):
    new_sponsor = models.Sponsor(**sponsor.dict())
    db.add(new_sponsor)
    db.commit()
    db.refresh(new_sponsor)
    return new_sponsor

def list_sponsors(db: Session):
    return db.query(models.Sponsor).all()

# ======================================================================
# THIS IS THE CORRECTED FUNCTION
# ======================================================================
def create_event_rating(db: Session, event_id: int, rating: schemas.RatingCreate):
    user = db.query(models.User).filter(models.User.phone == rating.user_phone).first()
    if not user:
        raise ValueError("User with this phone number not found.")

    booking = db.query(models.Booking).filter(
        models.Booking.event_id == event_id,
        models.Booking.user_id == user.id
    ).first()

    if not booking:
        raise ValueError("You have not booked a ticket for this event.")

    existing_rating = db.query(models.Rating).filter(
        models.Rating.event_id == event_id,
        models.Rating.user_id == user.id
    ).first()

    if existing_rating:
        existing_rating.rating = rating.rating
        db.commit()
        db.refresh(existing_rating)
        # Manually create the response to include the user's phone
        return schemas.Rating(
            id=existing_rating.id,
            event_id=existing_rating.event_id,
            rating=existing_rating.rating,
            user_phone=user.phone
        )

    new_rating = models.Rating(
        event_id=event_id,
        user_id=user.id,
        rating=rating.rating
    )
    db.add(new_rating)
    db.commit()
    db.refresh(new_rating)

    # Manually create the response to include the user's phone
    return schemas.Rating(
        id=new_rating.id,
        event_id=new_rating.event_id,
        rating=new_rating.rating,
        user_phone=user.phone
    )
