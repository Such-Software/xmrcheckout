"use server";

import { verifyTurnstile } from "../../../lib/turnstile";

const RESEND_API_KEY = process.env.RESEND_API_KEY;
const CONTACT_EMAIL = process.env.CONTACT_EMAIL || "apps@such.software";
const SITE_NAME = process.env.NEXT_PUBLIC_SITE_NAME || "XMR Checkout";

export type SignupState = {
  success: boolean;
  message: string;
  errors?: Record<string, string>;
};

export async function submitSignupRequest(
  _prevState: SignupState,
  formData: FormData
): Promise<SignupState> {
  const name = String(formData.get("name") ?? "").trim();
  const email = String(formData.get("email") ?? "").trim();
  const storeUrl = String(formData.get("store_url") ?? "").trim();
  const message = String(formData.get("message") ?? "").trim();
  const token = String(formData.get("token") ?? "").trim();

  const errors: Record<string, string> = {};
  if (name.length < 2) errors.name = "Name is too short.";
  if (!email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email))
    errors.email = "Invalid email address.";
  if (message.length < 10) errors.message = "Please tell us more.";
  if (!token) errors.token = "Please complete the security check.";

  if (Object.keys(errors).length > 0) {
    return { success: false, message: "", errors };
  }

  const isHuman = await verifyTurnstile(token);
  if (!isHuman) {
    return { success: false, message: "Security check failed. Please refresh." };
  }

  if (!RESEND_API_KEY) {
    console.warn("RESEND_API_KEY not set, logging signup request instead");
    console.log("Signup request:", { name, email, storeUrl, message });
    return {
      success: true,
      message:
        "Request received. We will review your application and get back to you.",
    };
  }

  try {
    const { Resend } = await import("resend");
    const resend = new Resend(RESEND_API_KEY);

    const subject = `[${SITE_NAME}] Merchant access request from ${name}`;

    const { error } = await resend.emails.send({
      from: `${SITE_NAME} <noreply@such.software>`,
      to: CONTACT_EMAIL,
      replyTo: email,
      subject,
      text: [
        `Name: ${name}`,
        `Email: ${email}`,
        `Store URL: ${storeUrl || "(not provided)"}`,
        "",
        "Message:",
        message,
      ].join("\n"),
      html: `
        <h2>Merchant Access Request</h2>
        <p><strong>Name:</strong> ${name}</p>
        <p><strong>Email:</strong> <a href="mailto:${email}">${email}</a></p>
        <p><strong>Store URL:</strong> ${storeUrl ? `<a href="${storeUrl}">${storeUrl}</a>` : "<em>not provided</em>"}</p>
        <h3>Message:</h3>
        <p>${message.replace(/\n/g, "<br>")}</p>
      `,
    });

    if (error) {
      console.error("Resend error:", error);
      return {
        success: false,
        message: "Failed to send request. Please try again.",
      };
    }

    return {
      success: true,
      message:
        "Request received. We will review your application and get back to you.",
    };
  } catch (e) {
    console.error("Email error:", e);
    return {
      success: false,
      message: "System error. Please try again or contact us directly.",
    };
  }
}
