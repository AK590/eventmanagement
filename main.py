import sys
import os
from fastapi import FastAPI, Depends, HTTPException, Response
from sqlalchemy.orm import Session

# Corrected relative imports
from .database import Base, engine, get_db
from fastapi.middleware.cors import CORSMiddleware
from . import crud, models, schemas
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from typing import List

# --- Determine the project's root and frontend directories ---
ROOT_DIRECTORY = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_DIRECTORY = os.path.join(ROOT_DIRECTORY, 'frontend')

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Event Management API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Event Endpoints ---
@app.post("/api/events", response_model=schemas.Event)
def create_event(event: schemas.EventCreate, db: Session = Depends(get_db)):
    return crud.create_event(db=db, ev=event)

@app.get("/api/events", response_model=List[schemas.EventDetail])
def read_events(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    events = crud.list_events(db, skip=skip, limit=limit)
    return events

@app.get("/api/events/{event_id}/bookings", response_model=List[schemas.BookingDetail])
def get_event_bookings(event_id: int, db: Session = Depends(get_db)):
    return crud.get_bookings_for_event(db, event_id=event_id)

@app.delete("/api/events/{event_id}")
def delete_event(event_id: int, db: Session = Depends(get_db)):
    deleted_event = crud.delete_event(db, event_id=event_id)
    if deleted_event is None:
        raise HTTPException(status_code=404, detail="Event not found")
    return Response(status_code=204)

# --- Price & Booking Endpoints ---
@app.post("/api/events/price", response_model=schemas.PriceResponse)
def get_event_price(price_request: schemas.PriceRequest, db: Session = Depends(get_db)):
    try:
        return crud.get_dynamic_price(db, price_request)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.post("/api/book", response_model=schemas.Booking)
def book_ticket(booking: schemas.BookingCreate, db: Session = Depends(get_db)):
    try:
        return crud.book_ticket(db, b=booking)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

# --- Sponsor Endpoints ---
@app.post("/api/sponsors", response_model=schemas.Sponsor)
def create_sponsor(sponsor: schemas.SponsorCreate, db: Session = Depends(get_db)):
    return crud.create_sponsor(db=db, sponsor=sponsor)

@app.get("/api/sponsors", response_model=List[schemas.Sponsor])
def get_sponsors(db: Session = Depends(get_db)):
    return crud.list_sponsors(db)

# --- Verification Endpoint ---
@app.get("/api/verify/{ticket_hash}", response_model=schemas.VerifiedBookingDetail)
def verify_ticket(ticket_hash: str, db: Session = Depends(get_db)):
    booking_details = crud.verify_ticket(db, ticket_hash=ticket_hash)
    if not booking_details:
        raise HTTPException(status_code=404, detail="Ticket hash not found or invalid.")
    return booking_details

# --- Frontend Serving ---
app.mount("/static", StaticFiles(directory=FRONTEND_DIRECTORY), name="static")

@app.get("/")
async def read_index():
    return FileResponse(os.path.join(FRONTEND_DIRECTORY, 'index.html'))

