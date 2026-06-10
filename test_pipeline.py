#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import smtplib
import ssl
import sys
from email.message import EmailMessage


def main() -> int:
    parser = argparse.ArgumentParser(description="Send AibriefAI alert email via SMTP secrets")
    parser.add_argument("--subject", required=True)
    parser.add_argument("--body", required=True)
    parser.add_argument("--to", default=os.getenv("ALERT_EMAIL_TO", "Fmg_511@hotmail.com"))
    args = parser.parse_args()

    host = os.getenv("SMTP_HOST", "").strip()
    port = int(os.getenv("SMTP_PORT", "587"))
    username = os.getenv("SMTP_USERNAME", "").strip()
    password = os.getenv("SMTP_PASSWORD", "")
    sender = os.getenv("SMTP_FROM", username).strip()

    if not host or not username or not password or not sender:
        print("SMTP alert skipped: SMTP_HOST, SMTP_USERNAME, SMTP_PASSWORD, SMTP_FROM are required", file=sys.stderr)
        return 0

    msg = EmailMessage()
    msg["Subject"] = args.subject
    msg["From"] = sender
    msg["To"] = args.to
    msg.set_content(args.body)

    context = ssl.create_default_context()
    with smtplib.SMTP(host, port, timeout=30) as server:
        server.starttls(context=context)
        server.login(username, password)
        server.send_message(msg)
    print(f"alert sent to {args.to}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
