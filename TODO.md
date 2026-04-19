# xmrcheckout — Local TODO / Followups

Notes for ourselves. Not committed (see .gitignore or just left untracked).
Kept here so context survives a terminal restart.

## Reconciler wallet handling

### Understanding (not a bug — design)

- Each merchant has their own Monero view-only wallet (`user-<uuid>-<fingerprint>.keys`).
- We run 3 `monero-wallet-rpc` containers as a pool. monero-wallet-rpc can hold
  one wallet open at a time. We hash-shard wallets across the 3 backends
  (consistent hashing on wallet_name).
- At any idle moment, 2 out of 3 backends are expected to hold no wallet.
  That's fine. Wallets open lazily when the reconciler needs to query them
  (via `_ensure_wallet_open`).
- `open_wallet` / `close_wallet` on the monero-wallet-rpc process is cheap
  when the wallet is already open in the wallet-rpc process (the wallet-rpc
  itself short-circuits), but our Python-side `backend.current_wallet` cache
  is reset every reconciler loop, so we send redundant RPC calls each loop.

### Medium-priority followups

1. **Make `MoneroWalletService` long-lived across reconciler loops.**
   Currently `reconciler.main()` constructs `MoneroWalletService()` fresh every
   iteration, which resets `backend.current_wallet = None`. The actual
   monero-wallet-rpc process usually still has the wallet open, but our Python
   code doesn't know that, so it resends `close_wallet` + `open_wallet` on
   every loop. Harmless but wasteful — ~2 extra RPCs per active invoice per
   tick. Fix: hoist the service out of the loop, keep it across iterations.

2. **Verify wallet-rpc recovery after wallet-rpc container restart.**
   When wallet-rpc containers restart, the `_ensure_wallet_open` path should
   reopen wallets on first use. It appears to work in practice but we haven't
   written a targeted test. Add a test that simulates wallet-rpc restart
   between two invoice reconciliation passes for the same tenant.

3. **Dedicated wallet-rpc backend per busy tenant.**
   The consistent-hash sharding works fine at low tenant count. When one
   tenant becomes hot (lots of invoices), one backend is hit 100% and the
   other two sit idle. If we hit scale, think about either pinning hot
   tenants to dedicated backends, or sharding by invoice rather than tenant.

## Webhook payload: amount propagation

- We now include `amount` (fiat from quote), `currency`, and `amount_crypto`
  in the BTCPay-compat webhook payload. This was added because Medusa's
  capture workflow needs the amount to flip `captured_at` — without it, it
  captures 0 and the payment stays stuck "authorized" even after we fire
  `InvoiceSettled`/`InvoicePaymentSettled`.
- Downstream followups:
  - Consider including `amount_atomic` (integer atomic units) for any
    processor that prefers integer arithmetic over Decimal strings.
  - Consider including `exchange_rate` at webhook time so downstream can
    reproduce the fiat figure if their Decimal precision differs.

## Logging

- Silenced `monero.backends.jsonrpc.wallet` library logger (set to CRITICAL)
  in `reconciler.py` so the `-13 No wallet file` errors from routine
  `close_wallet` calls on idle backends stop polluting logs.
- If we need to debug wallet-rpc issues in the future, temporarily set it
  back to WARNING and rebuild.

## Upstream PRs

Open PRs we submitted upstream (xmrcheckout/xmrcheckout):
- Advisory locks, restore_height lookback, transfer-deletion guard,
  decimal formatting, webhook retries, reconciler error logging.

Followups for upstream:
- Propose the webhook-amount addition as a PR once we've run it in prod for
  a week. That's a breaking-ish change for anyone downstream relying on a
  specific payload shape, so flag it carefully.
- Propose the `get_status` fix (drop the set_daemon call). Clear win — quiets
  log noise with no functional change. Low-risk PR.

## Known-unfixed

- We do not yet have a way for a tenant to manually trigger re-send of a
  webhook delivery (e.g. if Medusa was down when the settle fired). Would
  be a nice admin UI action.
- If wallet-rpc runs out of memory handling many simultaneous wallet opens,
  we have no backpressure — the reconciler will just keep trying. Should
  add a circuit-breaker / per-backend queue depth limit at some point.
