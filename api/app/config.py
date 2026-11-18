import os


def _get_bool_env(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None or value == "":
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _get_env(name: str, default: str | None = None) -> str:
    value = os.getenv(name, default)
    if value is None or value == "":
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


DATABASE_URL = _get_env("DATABASE_URL")

API_KEYS = [
    key.strip()
    for key in os.getenv("API_KEYS", "").split(",")
    if key.strip()
]

API_KEY_ENCRYPTION_KEY = _get_env("API_KEY_ENCRYPTION_KEY")
INVOICE_RECONCILE_INTERVAL_SECONDS = int(os.getenv("INVOICE_RECONCILE_INTERVAL_SECONDS", "30"))
INVOICE_DEFAULT_EXPIRY_HOURS = int(os.getenv("INVOICE_DEFAULT_EXPIRY_HOURS", "1"))
LATE_PAYMENT_LOOKBACK_HOURS = int(os.getenv("LATE_PAYMENT_LOOKBACK_HOURS", "48"))
DONATION_EXPIRY_MINUTES = int(os.getenv("DONATION_EXPIRY_MINUTES", "30"))
DONATION_ACTIVE_INVOICE_LIMIT = int(os.getenv("DONATION_ACTIVE_INVOICE_LIMIT", "25"))
RATE_PROVIDER = os.getenv("RATE_PROVIDER", "kraken")
DONATIONS_ENABLED = _get_bool_env("DONATIONS_ENABLED", False)
OPEN_REGISTRATION = _get_bool_env("OPEN_REGISTRATION", True)

MONERO_WALLET_RPC_URLS = [
    url.strip()
    for url in os.getenv("MONERO_WALLET_RPC_URLS", "").split(",")
    if url.strip()
]
MONERO_WALLET_RPC_USER = os.getenv("MONERO_WALLET_RPC_USER", "")
MONERO_WALLET_RPC_PASSWORD = os.getenv("MONERO_WALLET_RPC_PASSWORD", "")
MONERO_WALLET_RPC_WALLET_PASSWORD = os.getenv("MONERO_WALLET_RPC_WALLET_PASSWORD", "")
MONERO_DAEMON_URL = os.getenv("MONERO_DAEMON_URL")


def check_daemon_url(url: str | None) -> None:
    """Refuse a plain-http daemon on a public host.

    Payment detection trusts the daemon. Over plain http to a host on the
    internet, the operator of that host or anyone on the path can fake
    transfers or confirmations. http is accepted for loopback, private and
    link-local addresses and for single-label or local-only names (Docker
    service names such as `monerod`); anything else must use https.
    """
    if not url:
        return
    from ipaddress import ip_address
    from urllib.parse import urlsplit

    parts = urlsplit(url if "://" in url else f"http://{url}")
    if parts.scheme == "https":
        return
    host = (parts.hostname or "").lower().rstrip(".")
    try:
        address = ip_address(host)
    except ValueError:
        local = (
            "." not in host
            or host == "localhost"
            or host.endswith((".local", ".lan", ".internal", ".home.arpa"))
        )
    else:
        local = address.is_private or address.is_loopback or address.is_link_local
    if not local:
        raise RuntimeError(
            "MONERO_DAEMON_URL uses plain http to a public host; use your own daemon on a "
            "private network or an https endpoint"
        )


check_daemon_url(MONERO_DAEMON_URL)
MONERO_WALLET_RPC_WALLET_DIR = os.getenv("MONERO_WALLET_RPC_WALLET_DIR", "")
FOUNDER_PAYMENT_ADDRESS = os.getenv("FOUNDER_PAYMENT_ADDRESS", "")
FOUNDER_VIEW_KEY = os.getenv("FOUNDER_VIEW_KEY", "")
QR_STORAGE_DIR = os.getenv("QR_STORAGE_DIR", "/qr")
ADMIN_API_KEY = os.getenv("ADMIN_API_KEY", "").strip()
