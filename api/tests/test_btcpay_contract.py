import unittest

from pydantic import ValidationError

from app.btcpay_schemas import BtcpayCheckout, BtcpayWebhookCreate


class BtcpayContractTests(unittest.TestCase):
    def test_exact_confirmation_target_is_bounded(self):
        self.assertEqual(BtcpayCheckout(confirmationsRequired=10000).confirmationsRequired, 10000)
        with self.assertRaises(ValidationError):
            BtcpayCheckout(confirmationsRequired=10001)

    def test_webhook_accepts_operator_generated_secret(self):
        webhook = BtcpayWebhookCreate(
            url="https://evaluetron.example/webhooks/btcpay",
            secret="operator-generated-secret",
            authorizedEvents={"specificEvents": ["InvoiceSettled"]},
        )
        self.assertEqual(webhook.secret, "operator-generated-secret")


if __name__ == "__main__":
    unittest.main()
