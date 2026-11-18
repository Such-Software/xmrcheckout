import unittest
from dataclasses import dataclass

from app.payment_confirmations import effective_confirmations


@dataclass
class _Payment:
    amount_atomic: int
    confirmations: int


class EffectiveConfirmationTests(unittest.TestCase):
    def test_a_deep_small_payment_does_not_confirm_an_unconfirmed_top_up(self):
        payments = [_Payment(1, 30), _Payment(999, 0)]
        self.assertEqual(effective_confirmations(payments, 1000), 0)

    def test_depth_is_that_of_the_shallowest_payment_needed(self):
        payments = [_Payment(400, 12), _Payment(600, 3)]
        self.assertEqual(effective_confirmations(payments, 1000), 3)

    def test_an_extra_unconfirmed_payment_does_not_lower_a_covered_invoice(self):
        payments = [_Payment(1000, 10), _Payment(5, 0)]
        self.assertEqual(effective_confirmations(payments, 1000), 10)

    def test_an_underpaid_invoice_has_no_depth(self):
        self.assertEqual(effective_confirmations([_Payment(500, 50)], 1000), 0)

    def test_non_positive_amounts_are_ignored(self):
        payments = [_Payment(-5, 40), _Payment(0, 40), _Payment(1000, 2)]
        self.assertEqual(effective_confirmations(payments, 1000), 2)


if __name__ == "__main__":
    unittest.main()
