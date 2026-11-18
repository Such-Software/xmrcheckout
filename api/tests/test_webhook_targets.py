import socket
import unittest
from unittest import mock

from requests import ConnectionError as RequestsConnectionError

from app import webhook_targets
from app.webhook_targets import (
    WebhookTargetRefused,
    check_webhook_target,
    delivery_error_message,
    post_webhook,
)


def _resolves_to(*addresses):
    def fake(host, port, type=0):
        return [(socket.AF_INET6 if ":" in a else socket.AF_INET, type, 6, "", (a, port)) for a in addresses]
    return fake


class WebhookTargetTests(unittest.TestCase):
    def _check(self, url, *addresses, allowed=frozenset()):
        with mock.patch.object(webhook_targets.socket, "getaddrinfo", side_effect=_resolves_to(*addresses)):
            check_webhook_target(url, allowed_private_hosts=allowed)

    def test_internal_targets_are_refused(self):
        for address in [
            "127.0.0.1",
            "10.1.2.3",
            "172.17.0.5",
            "192.168.88.10",
            "169.254.169.254",
            "100.64.0.1",
            "0.0.0.0",
            "::1",
            "fd00::1",
            "fe80::1",
            "::ffff:127.0.0.1",
        ]:
            with self.subTest(address=address), self.assertRaises(WebhookTargetRefused):
                self._check("https://merchant.example/hook", address)

    def test_one_private_record_among_public_ones_is_refused(self):
        with self.assertRaises(WebhookTargetRefused):
            self._check("https://merchant.example/hook", "93.184.216.34", "10.0.0.1")

    def test_a_public_target_is_accepted(self):
        self._check("https://merchant.example/hook", "93.184.216.34")

    def test_an_allowlisted_host_may_resolve_privately(self):
        self._check("http://receiver.lan.example/hook", "192.168.1.20", allowed=frozenset({"receiver.lan.example"}))

    def test_non_http_schemes_and_embedded_credentials_are_refused(self):
        for url in ["file:///etc/passwd", "gopher://merchant.example/", "https://user:pw@merchant.example/"]:
            with self.subTest(url=url), self.assertRaises(WebhookTargetRefused):
                self._check(url, "93.184.216.34")

    def test_delivery_never_follows_redirects(self):
        with mock.patch.object(webhook_targets.socket, "getaddrinfo", side_effect=_resolves_to("93.184.216.34")), \
                mock.patch.object(webhook_targets.requests, "post") as post:
            post_webhook("https://merchant.example/hook", data=b"{}", allow_redirects=True, timeout=5)
        self.assertIs(post.call_args.kwargs["allow_redirects"], False)

    def test_a_refused_target_is_never_contacted(self):
        with mock.patch.object(webhook_targets.socket, "getaddrinfo", side_effect=_resolves_to("10.0.0.1")), \
                mock.patch.object(webhook_targets.requests, "post") as post:
            with self.assertRaises(WebhookTargetRefused):
                post_webhook("https://merchant.example/hook", data=b"{}", timeout=5)
        post.assert_not_called()

    def test_stored_errors_do_not_echo_the_exception_text(self):
        detail = "HTTPConnectionPool(host='10.0.0.7', port=5432): secret internal detail"
        message = delivery_error_message(RequestsConnectionError(detail))
        self.assertNotIn("10.0.0.7", message)
        self.assertNotIn("5432", message)


class DeliveryPathTests(unittest.TestCase):
    """The real delivery code must route every request through the guard."""

    def test_native_webhooks_refuse_internal_targets(self):
        from app import webhooks

        hook = mock.Mock(events=["invoice.created"], event_urls={}, url="http://10.0.0.5:5432/x", id="h")
        db = mock.Mock()
        db.query.return_value.filter.return_value.all.return_value = [hook]
        db.query.return_value.filter.return_value.first.return_value = None
        invoice = mock.MagicMock()
        with mock.patch.object(webhook_targets.socket, "getaddrinfo", side_effect=_resolves_to("10.0.0.5")), \
                mock.patch.object(webhook_targets.requests, "post") as post, \
                mock.patch.object(webhooks, "build_webhook_payload", return_value={}):
            webhooks.dispatch_webhooks(db, "00000000-0000-0000-0000-000000000001", "invoice.created", invoice)
        post.assert_not_called()

    def test_btcpay_webhooks_refuse_internal_targets(self):
        from app import btcpay_webhooks

        hook = mock.Mock(url="http://169.254.169.254/latest", id="h", authorized_events={"everything": True})
        db = mock.Mock()
        db.query.return_value.filter.return_value.all.return_value = [hook]
        with mock.patch.object(webhook_targets.socket, "getaddrinfo", side_effect=_resolves_to("169.254.169.254")), \
                mock.patch.object(webhook_targets.requests, "post") as post, \
                mock.patch.object(btcpay_webhooks, "_build_payload", return_value={}), \
                mock.patch.object(btcpay_webhooks, "decrypt_secret", return_value="s" * 32), \
                mock.patch.object(btcpay_webhooks.time, "sleep"):
            btcpay_webhooks.dispatch_btcpay_webhooks(db, "u", "InvoiceSettled", mock.MagicMock())
        post.assert_not_called()


if __name__ == "__main__":
    unittest.main()
