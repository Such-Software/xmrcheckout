"use client";

import { Turnstile } from "@marsidev/react-turnstile";
import { useState, useEffect } from "react";

const SITE_KEY = process.env.NEXT_PUBLIC_TURNSTILE_SITE_KEY;

export default function TurnstileWidget({
  onVerify,
}: {
  onVerify: (token: string) => void;
}) {
  const [mounted, setMounted] = useState(false);
  const [error, setError] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!SITE_KEY) {
    return null;
  }

  if (!mounted) {
    return <div className="h-[65px] w-[300px]" />;
  }

  if (error) {
    return (
      <p className="text-xs text-ink-soft">Security check unavailable</p>
    );
  }

  return (
    <Turnstile
      siteKey={SITE_KEY}
      onSuccess={onVerify}
      onError={() => setError(true)}
      onExpire={() => onVerify("")}
      options={{ theme: "light" }}
    />
  );
}
