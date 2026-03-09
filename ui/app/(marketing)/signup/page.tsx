import { Metadata } from "next";
import SignupForm from "./signup-form";

export const metadata: Metadata = {
  title: "Request Access",
};

export default function SignupPage() {
  return (
    <section className="section">
      <div className="section-inner" style={{ maxWidth: 560 }}>
        <p className="eyebrow">Merchant access</p>
        <h1 className="section-title">Request access</h1>
        <p className="mt-4 text-ink-soft">
          Tell us about your store and we will get you set up. Once approved
          you will receive your credentials by email.
        </p>
        <SignupForm />
      </div>
    </section>
  );
}
