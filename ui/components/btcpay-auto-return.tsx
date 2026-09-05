"use client";

import { useEffect } from "react";

/**
 * Sends the customer back to the merchant once their payment has been seen.
 *
 * A merchant that supplied `redirectURL` and `redirectAutomatically` on the invoice is asking for
 * its customer back, and the moment to do that is detection rather than final depth: the payment is
 * irreversible from the payer's side already, and the merchant's own page is where the order status
 * belongs. Waiting for the confirmation target instead leaves the customer parked on a payment page
 * for as long as the coin takes, which for Monero is ten blocks.
 *
 * The delay is deliberate. The customer should see the payment acknowledged here before the page
 * changes under them, otherwise the redirect reads as the checkout failing.
 *
 * Rendered by both checkout styles so the rule lives in one place.
 */
type BtcpayAutoReturnProps = {
  status: string;
  redirectUrl: string | null;
  redirectAutomatically: boolean | null;
  delayMs?: number;
};

export default function BtcpayAutoReturn({
  status,
  redirectUrl,
  redirectAutomatically,
  delayMs = 3000,
}: BtcpayAutoReturnProps) {
  useEffect(() => {
    if (
      (status !== "confirmed" && status !== "payment_detected") ||
      !redirectUrl ||
      !redirectAutomatically
    ) {
      return;
    }
    const timer = window.setTimeout(() => {
      try {
        window.top?.location.assign(redirectUrl);
      } catch {
        window.location.assign(redirectUrl);
      }
    }, delayMs);
    return () => {
      window.clearTimeout(timer);
    };
  }, [delayMs, redirectAutomatically, redirectUrl, status]);

  return null;
}
