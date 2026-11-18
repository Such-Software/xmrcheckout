from __future__ import annotations

from sqlalchemy.orm import Session

from .models import User
from .security import decrypt_secret
from .subaddress_derivation import derive_subaddress


# Caps how many donation invoices may be active at once. It no longer bounds
# subaddress indices, which only ever increase.
MAX_SUBADDRESS_INDEX = 300


def create_subaddress_for_user(
    db: Session,
    *,
    user: User,
) -> tuple[str, int | None]:
    locked = (
        db.query(User)
        .filter(
            User.id == user.id,
        )
        .with_for_update()
        .first()
    )
    if locked is None:
        raise ValueError("User not found")
    start_index = int(locked.subaddress_start_index or 0)
    if start_index < 0:
        start_index = 0
    # Indices only ever increase. Wrapping back to the start of a range made a
    # later invoice share a subaddress with an earlier one, so the earlier
    # invoice's payment counted toward the later invoice.
    next_index = max(int(locked.next_subaddress_index or 0), start_index + 1)
    locked.next_subaddress_index = next_index + 1
    db.flush()
    view_key = decrypt_secret(locked.view_key_encrypted)
    address = derive_subaddress(
        payment_address=locked.payment_address,
        view_key=view_key,
        account_index=0,
        address_index=next_index,
    )
    return address, int(next_index)
