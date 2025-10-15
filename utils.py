# utils.py
import hashlib, secrets

def gen_ticket_hash(user_email: str, event_id: int, timestamp: str, nonce: str = None) -> str:
    nonce = nonce or secrets.token_hex(8)
    raw = f"{user_email}|{event_id}|{timestamp}|{nonce}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()

