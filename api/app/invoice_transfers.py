from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Iterable, TypeVar

# Monero accepts a block whose timestamp is above the median of the previous 60
# blocks (about an hour behind the chain tip) and at most two hours ahead of
# the node clock. A payment mined after an invoice was created can therefore
# carry a timestamp up to roughly an hour earlier than the invoice. Two hours
# keeps every genuine payment and still excludes anything older.
BLOCK_TIMESTAMP_SLACK = timedelta(hours=2)

T = TypeVar("T")


def transfers_for_invoice(transfers: Iterable[T], created_at: datetime | None) -> list[T]:
    """Return only the transfers that can belong to an invoice created at created_at.

    A subaddress can carry payments that predate its current invoice: older
    invoices reused it, or someone paid it before. Those must never count toward
    the new invoice. A transfer with no timestamp is excluded once the invoice
    has a creation time, because nothing proves it is recent.
    """
    items = list(transfers)
    if created_at is None:
        return items
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=timezone.utc)
    cutoff = int((created_at - BLOCK_TIMESTAMP_SLACK).timestamp())
    return [
        item
        for item in items
        if getattr(item, "timestamp", None) is not None and int(item.timestamp) >= cutoff
    ]
