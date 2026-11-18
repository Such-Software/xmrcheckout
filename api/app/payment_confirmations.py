from __future__ import annotations

from typing import Iterable, Protocol


class _Payment(Protocol):
    amount_atomic: int
    confirmations: int


def effective_confirmations(transfers: Iterable[_Payment], required_atomic: int) -> int:
    """Return the confirmation depth at which the invoice amount is fully covered.

    Payments are taken from the deepest down, and the depth of the last payment
    needed to reach required_atomic is the invoice's depth. An invoice is
    therefore confirmed to N only when payments with at least N confirmations
    cover the whole amount. A small early payment cannot lend its depth to an
    unconfirmed top-up. Returns 0 while the payments do not cover the amount.
    """
    payments = sorted(
        (t for t in transfers if t.amount_atomic > 0),
        key=lambda t: t.confirmations,
        reverse=True,
    )
    covered = 0
    for payment in payments:
        covered += payment.amount_atomic
        if covered >= required_atomic:
            return max(0, int(payment.confirmations))
    return 0
