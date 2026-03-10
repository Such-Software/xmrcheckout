"""Admin API endpoints for managing merchants.

Protected by ADMIN_API_KEY — separate from per-user API keys.
"""

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from .config import ADMIN_API_KEY
from .db import get_db
from .models import Invoice, User
from .security import (
    encrypt_api_key,
    encrypt_secret,
    generate_api_key,
    generate_webhook_secret,
    hash_api_key,
    decrypt_api_key,
)

router = APIRouter(prefix="/api/admin", tags=["admin"])


# ---------------------------------------------------------------------------
# Auth dependency
# ---------------------------------------------------------------------------

def require_admin(
    authorization: str | None = Header(default=None),
    x_admin_key: str | None = Header(default=None, alias="X-Admin-Key"),
) -> str:
    """Validate admin API key from Authorization header or X-Admin-Key."""
    if not ADMIN_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Admin API not configured",
        )

    key: str | None = None
    if authorization:
        scheme, _, token = authorization.partition(" ")
        if scheme.lower() in ("adminkey", "bearer"):
            key = token.strip() or None
    if key is None:
        key = x_admin_key

    if key != ADMIN_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid admin key",
        )
    return key


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class AdminUserResponse(BaseModel):
    id: str
    payment_address: str
    invoice_count: int
    created_at: str | None

    class Config:
        from_attributes = True


class AdminUserDetail(AdminUserResponse):
    api_key: str
    webhook_secret: str | None
    next_subaddress_index: int


class AdminCreateUser(BaseModel):
    payment_address: str
    view_key: str


class AdminCreateUserResponse(BaseModel):
    id: str
    payment_address: str
    api_key: str
    webhook_secret: str
    store_id: str


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/users", response_model=list[AdminUserResponse])
def list_users(
    _admin: str = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """List all registered merchants with invoice counts."""
    rows = (
        db.query(
            User.id,
            User.payment_address,
            User.created_at,
            func.count(Invoice.id).label("invoice_count"),
        )
        .outerjoin(Invoice, Invoice.user_id == User.id)
        .group_by(User.id)
        .order_by(User.created_at.desc())
        .all()
    )
    return [
        AdminUserResponse(
            id=str(r.id),
            payment_address=r.payment_address,
            invoice_count=r.invoice_count,
            created_at=r.created_at.isoformat() if r.created_at else None,
        )
        for r in rows
    ]


@router.get("/users/{user_id}", response_model=AdminUserDetail)
def get_user(
    user_id: str,
    _admin: str = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Get detailed info for a single merchant."""
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    invoice_count = db.query(func.count(Invoice.id)).filter(Invoice.user_id == user.id).scalar()
    api_key = decrypt_api_key(user.api_key_encrypted)
    webhook_secret = None
    if user.webhook_secret_encrypted:
        from .security import decrypt_secret
        webhook_secret = decrypt_secret(user.webhook_secret_encrypted)
    return AdminUserDetail(
        id=str(user.id),
        payment_address=user.payment_address,
        invoice_count=invoice_count or 0,
        created_at=user.created_at.isoformat() if user.created_at else None,
        api_key=api_key,
        webhook_secret=webhook_secret,
        next_subaddress_index=user.next_subaddress_index,
    )


@router.post("/users", response_model=AdminCreateUserResponse, status_code=201)
def create_user(
    payload: AdminCreateUser,
    _admin: str = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Create a new merchant. Same logic as login but bypasses OPEN_REGISTRATION."""
    from .routes import _validate_payment_address_and_view_key

    payment_address = payload.payment_address.strip()
    view_key = payload.view_key.strip()
    _validate_payment_address_and_view_key(payment_address, view_key)

    existing = db.query(User).filter(User.payment_address == payment_address).first()
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User with this address already exists",
        )

    api_key = generate_api_key()
    webhook_secret = generate_webhook_secret()
    user = User(
        payment_address=payment_address,
        view_key_encrypted=encrypt_secret(view_key),
        api_key_hash=hash_api_key(api_key),
        api_key_encrypted=encrypt_api_key(api_key),
        webhook_secret_encrypted=encrypt_secret(webhook_secret),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return AdminCreateUserResponse(
        id=str(user.id),
        payment_address=payment_address,
        api_key=api_key,
        webhook_secret=webhook_secret,
        store_id=str(user.id),
    )


@router.delete("/users/{user_id}", status_code=204)
def delete_user(
    user_id: str,
    _admin: str = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Remove a merchant and all their data."""
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    # Delete related data
    from .models import Webhook, WebhookDelivery, ProfileHistory, BtcpayWebhook
    db.query(WebhookDelivery).filter(WebhookDelivery.user_id == user.id).delete()
    db.query(Webhook).filter(Webhook.user_id == user.id).delete()
    db.query(BtcpayWebhook).filter(BtcpayWebhook.user_id == user.id).delete()
    db.query(ProfileHistory).filter(ProfileHistory.user_id == user.id).delete()
    db.query(Invoice).filter(Invoice.user_id == user.id).delete()
    db.delete(user)
    db.commit()
    return None


@router.post("/auth/verify", status_code=200)
def verify_admin_key(_admin: str = Depends(require_admin)):
    """Verify that the provided admin key is valid."""
    return {"ok": True}
