"use client";

import { useActionState } from "react";
import { useFormStatus } from "react-dom";
import { useState, useEffect, useRef } from "react";

import TurnstileWidget from "../../../components/turnstile-widget";
import { submitSignupRequest, type SignupState } from "./actions";

const initialState: SignupState = { success: false, message: "" };

function SubmitButton() {
  const { pending } = useFormStatus();
  return (
    <button
      className="inline-flex items-center justify-center rounded-full bg-ink px-6 py-3 text-sm font-semibold text-cream shadow-[0_16px_30px_rgba(16,18,23,0.18)] transition hover:-translate-y-0.5 disabled:cursor-not-allowed disabled:bg-ink/60 disabled:text-cream/70 disabled:shadow-none disabled:hover:translate-y-0"
      type="submit"
      disabled={pending}
    >
      {pending ? "Sending..." : "Request Access"}
    </button>
  );
}

export default function SignupForm() {
  const [state, formAction] = useActionState(submitSignupRequest, initialState);
  const [token, setToken] = useState("");
  const formRef = useRef<HTMLFormElement>(null);

  useEffect(() => {
    if (state.success && formRef.current) {
      formRef.current.reset();
      setToken("");
    }
  }, [state.success]);

  return (
    <form ref={formRef} className="mt-6 grid gap-5" action={formAction}>
      <div className="grid gap-2">
        <label
          className="text-xs font-semibold uppercase tracking-[0.2em] text-ink-soft"
          htmlFor="name"
        >
          Your name
        </label>
        <input
          className="min-h-[48px] w-full rounded-xl border border-stroke bg-white/80 px-4 py-3 text-sm text-ink shadow-[inset_0_1px_0_rgba(255,255,255,0.6)] outline-none transition focus:border-ink/40 focus:ring-2 focus:ring-ink/10"
          id="name"
          name="name"
          required
        />
        {state.errors?.name ? (
          <p className="text-xs text-red-600">{state.errors.name}</p>
        ) : null}
      </div>

      <div className="grid gap-2">
        <label
          className="text-xs font-semibold uppercase tracking-[0.2em] text-ink-soft"
          htmlFor="email"
        >
          Email
        </label>
        <input
          className="min-h-[48px] w-full rounded-xl border border-stroke bg-white/80 px-4 py-3 text-sm text-ink shadow-[inset_0_1px_0_rgba(255,255,255,0.6)] outline-none transition focus:border-ink/40 focus:ring-2 focus:ring-ink/10"
          id="email"
          name="email"
          type="email"
          required
        />
        {state.errors?.email ? (
          <p className="text-xs text-red-600">{state.errors.email}</p>
        ) : null}
      </div>

      <div className="grid gap-2">
        <label
          className="text-xs font-semibold uppercase tracking-[0.2em] text-ink-soft"
          htmlFor="store_url"
        >
          Store URL <span className="normal-case tracking-normal text-ink-soft/60">(optional)</span>
        </label>
        <input
          className="min-h-[48px] w-full rounded-xl border border-stroke bg-white/80 px-4 py-3 text-sm text-ink shadow-[inset_0_1px_0_rgba(255,255,255,0.6)] outline-none transition focus:border-ink/40 focus:ring-2 focus:ring-ink/10"
          id="store_url"
          name="store_url"
          type="url"
          placeholder="https://"
        />
      </div>

      <div className="grid gap-2">
        <label
          className="text-xs font-semibold uppercase tracking-[0.2em] text-ink-soft"
          htmlFor="message"
        >
          Message
        </label>
        <textarea
          className="min-h-[120px] w-full resize-none rounded-xl border border-stroke bg-white/80 px-4 py-3 text-sm text-ink shadow-[inset_0_1px_0_rgba(255,255,255,0.6)] outline-none transition focus:border-ink/40 focus:ring-2 focus:ring-ink/10"
          id="message"
          name="message"
          placeholder="Tell us about your store and how you plan to accept payments..."
          required
        />
        {state.errors?.message ? (
          <p className="text-xs text-red-600">{state.errors.message}</p>
        ) : null}
      </div>

      <input type="hidden" name="token" value={token} />

      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between border-t border-stroke pt-4">
        <TurnstileWidget onVerify={setToken} />
        <SubmitButton />
      </div>

      {state.message ? (
        <p
          className={`rounded-lg border px-3 py-2 text-sm font-semibold ${
            state.success
              ? "border-emerald-200 bg-emerald-50 text-emerald-700"
              : "border-red-200 bg-red-50 text-red-700"
          }`}
        >
          {state.message}
        </p>
      ) : null}
    </form>
  );
}
