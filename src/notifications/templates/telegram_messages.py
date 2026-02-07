def get_payment_success_message(email: str) -> str:
    return (
        f"✅ <b>Payment Successful!</b>\n"
        f"📧 Email: {email}\n"
        f"💳 Status: Payment received, receipt delivered."
    )


def get_payment_failure_message(email: str, event: str, reason: str | None) -> str:
    reason_text = reason or "No specific reason provided"

    event_meaning = {
        "bounce": "Email does not exist (Hard Bounce)",
        "dropped": "Email previously bounced/unsubscribed",
        "spamreport": "User marked as Spam",
        "blocked": "IP/Domain blocked"
    }.get(event, event)

    return (
        f"⚠️ <b>PAYMENT OK, BUT EMAIL FAILED!</b>\n"
        f"<i>Client paid, but didn't receive the email.</i>\n\n"
        f"📧 Email: {email}\n"
        f"❗ Event: <b>{event.upper()}</b> ({event_meaning})\n"
        f"❌ Error: {reason_text}\n\n"
        f"👉 <b>Action:</b> Contact client manually via different channel!"
    )


def get_activation_failed_message(email: str, event: str, reason: str | None) -> str:
    reason_text = reason or "unknown"
    return (
        f"🚫 <b>Invalid Email (Registration)</b>\n"
        f"📧 Email: {email}\n"
        f"❗ Event: {event}\n"
        f"💬 Reason: {reason_text}\n"
        f"🧹 <b>Action:</b> Inactive user deleted from database."
    )


def get_active_user_error_message(email: str, event: str, reason: str | None) -> str:
    reason_text = reason or "unknown"
    return (
        f"‼️ <b>Email Delivery Failed for Active User</b>\n"
        f"📧 Email: {email}\n"
        f"❗ Event: {event}\n"
        f"💬 Reason: {reason_text}"
    )
