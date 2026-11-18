import unittest
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from unittest import mock

from app import subaddress_allocator
from app.invoice_transfers import transfers_for_invoice


@dataclass
class _Transfer:
    txid: str
    amount_atomic: int
    timestamp: int | None


class _User:
    def __init__(self, start_index=0, next_index=1):
        self.id = "user"
        self.subaddress_start_index = start_index
        self.next_subaddress_index = next_index
        self.view_key_encrypted = "encrypted"
        self.payment_address = "address"


class _Query:
    def __init__(self, user):
        self._user = user

    def filter(self, *args, **kwargs):
        return self

    def with_for_update(self):
        return self

    def first(self):
        return self._user


class _Session:
    def __init__(self, user):
        self._user = user

    def query(self, model):
        return _Query(self._user)

    def flush(self):
        pass


def _allocate(user, count):
    session = _Session(user)
    with mock.patch.object(subaddress_allocator, "decrypt_secret", return_value="view"), \
            mock.patch.object(
                subaddress_allocator,
                "derive_subaddress",
                side_effect=lambda **kw: f"sub-{kw['address_index']}",
            ):
        return [subaddress_allocator.create_subaddress_for_user(session, user=user)[1] for _ in range(count)]


class SubaddressAllocationTests(unittest.TestCase):
    def test_indices_never_repeat_for_a_merchant(self):
        indices = _allocate(_User(), 1000)
        self.assertEqual(len(indices), len(set(indices)))
        self.assertEqual(indices, sorted(indices))

    def test_allocation_starts_after_the_merchant_start_index(self):
        indices = _allocate(_User(start_index=500, next_index=1), 3)
        self.assertTrue(all(index > 500 for index in indices))

    def test_a_stored_next_index_beyond_the_old_range_is_kept(self):
        indices = _allocate(_User(next_index=301), 2)
        self.assertGreaterEqual(min(indices), 301)


class InvoiceTransferWindowTests(unittest.TestCase):
    def setUp(self):
        self.created = datetime(2026, 11, 18, 12, 0, tzinfo=timezone.utc)

    def _at(self, delta):
        return int((self.created + delta).timestamp())

    def test_a_payment_from_before_the_invoice_does_not_count(self):
        old = _Transfer("old", 10, self._at(-timedelta(days=3)))
        new = _Transfer("new", 5, self._at(timedelta(minutes=4)))
        self.assertEqual([t.txid for t in transfers_for_invoice([old, new], self.created)], ["new"])

    def test_a_block_timestamp_slightly_behind_the_invoice_still_counts(self):
        lagging = _Transfer("lagging", 10, self._at(-timedelta(minutes=50)))
        self.assertEqual(len(transfers_for_invoice([lagging], self.created)), 1)

    def test_a_transfer_without_a_timestamp_does_not_count(self):
        self.assertEqual(transfers_for_invoice([_Transfer("x", 10, None)], self.created), [])

    def test_a_naive_creation_time_is_read_as_utc(self):
        naive = self.created.replace(tzinfo=None)
        old = _Transfer("old", 10, self._at(-timedelta(days=1)))
        self.assertEqual(transfers_for_invoice([old], naive), [])


if __name__ == "__main__":
    unittest.main()
