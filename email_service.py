"""
Email automation service for SEO audit reports.
"""

import logging
import os
import smtplib
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Tuple

logger = logging.getLogger(__name__)


def _get_smtp_config():
    """Return (sender, password, host, port) from environment variables."""
    return (
        os.getenv("EMAIL_SENDER", ""),
        os.getenv("EMAIL_PASSWORD", ""),
        os.getenv("EMAIL_SMTP_HOST", "smtp.gmail.com"),
        int(os.getenv("EMAIL_SMTP_PORT", "587")),
    )


def _score_label(score: int) -> str:
    if score >= 70:
        return "Good"
    if score >= 40:
        return "Needs Improvement"
    return "Poor"


def _score_color(score: int) -> str:
    if score >= 70:
        return "#00d4aa"
    if score >= 40:
        return "#f59e0b"
    return "#ef4444"


def _build_html_email(
    customer_name: str,
    website_url: str,
    seo_score: int,
    business_name: str = "",
) -> str:
    """Return a branded HTML email body."""
    name_display = customer_name or "Valued Customer"
    biz_display = f" for <strong>{business_name}</strong>" if business_name else ""
    label = _score_label(seo_score)
    score_color = _score_color(seo_score)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Your SEO Audit Report | ATI &amp; AI</title>
</head>
<body style="margin:0;padding:0;background:#0a0a0a;font-family:'Segoe UI',system-ui,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#0a0a0a;padding:32px 0;">
    <tr>
      <td align="center">
        <table width="600" cellpadding="0" cellspacing="0" style="max-width:600px;width:100%;">

          <!-- Header -->
          <tr>
            <td style="background:linear-gradient(135deg,#0d1117,#161b22);border-radius:16px 16px 0 0;padding:32px 40px;border-bottom:2px solid #00d4ff33;">
              <h1 style="margin:0;font-size:28px;font-weight:800;color:#00d4ff;letter-spacing:-0.5px;">
                ATI &amp; <span style="color:#fff;">AI</span>
              </h1>
              <p style="margin:4px 0 0;color:#9ca3af;font-size:14px;">Professional SEO Audit Report</p>
            </td>
          </tr>

          <!-- Body -->
          <tr>
            <td style="background:#141414;padding:32px 40px;">

              <p style="color:#e5e7eb;font-size:16px;margin:0 0 24px;">
                Hi <strong style="color:#fff;">{name_display}</strong>,
              </p>
              <p style="color:#9ca3af;font-size:14px;margin:0 0 24px;line-height:1.7;">
                Your SEO audit{biz_display} for <strong style="color:#00d4ff;">{website_url}</strong>
                is complete. Your full interactive dashboard and detailed PDF report are attached to this email.
              </p>

              <!-- Score card -->
              <table width="100%" cellpadding="0" cellspacing="0" style="background:#0d0d0d;border-radius:12px;border:1px solid #222;margin:0 0 24px;overflow:hidden;">
                <tr>
                  <td style="padding:24px;text-align:center;">
                    <div style="font-size:64px;font-weight:800;color:{score_color};line-height:1;">{seo_score}</div>
                    <div style="font-size:18px;color:#9ca3af;margin-top:4px;">/ 100 — <span style="color:{score_color};">{label}</span></div>
                    <div style="font-size:12px;color:#6b7280;margin-top:8px;text-transform:uppercase;letter-spacing:0.5px;">Overall SEO Score</div>
                  </td>
                </tr>
              </table>

              <!-- Tips block -->
              <table width="100%" cellpadding="0" cellspacing="0" style="background:#0d0d0d;border-radius:12px;border:1px solid #222;margin:0 0 24px;">
                <tr>
                  <td style="padding:20px 24px;">
                    <p style="color:#00d4ff;font-size:13px;font-weight:700;margin:0 0 12px;text-transform:uppercase;letter-spacing:0.5px;">📎 Attachments Included</p>
                    <ul style="color:#9ca3af;font-size:13px;margin:0;padding-left:20px;line-height:2;">
                      <li><strong style="color:#e5e7eb;">SEO_Dashboard.html</strong> — Interactive dashboard with charts (open in browser)</li>
                      <li><strong style="color:#e5e7eb;">SEO_Audit_Report.pdf</strong> — Printable detailed PDF report</li>
                    </ul>
                  </td>
                </tr>
              </table>

              <p style="color:#6b7280;font-size:12px;margin:24px 0 0;line-height:1.7;">
                Have questions about your report? Reply to this email and our team will be happy to help.
              </p>
            </td>
          </tr>

          <!-- Footer -->
          <tr>
            <td style="background:#0d1117;border-radius:0 0 16px 16px;padding:20px 40px;border-top:1px solid #222;">
              <p style="color:#6b7280;font-size:11px;margin:0;text-align:center;">
                &copy; 2024 ATI &amp; AI — Automated Technical Insights &amp; AI<br>
                This email and attachments are confidential and intended solely for the addressee.
              </p>
            </td>
          </tr>

        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""


def send_audit_report(
    to_email: str,
    customer_name: str,
    website_url: str,
    seo_score: int,
    html_dashboard_content: str,
    pdf_bytes: bytes,
    business_name: str = "",
) -> Tuple[bool, str]:
    """
    Send the SEO audit report to *to_email* via SMTP.

    Returns (success: bool, message: str).
    Skips silently (returns False) when email credentials are not configured.
    """
    sender, password, smtp_host, smtp_port = _get_smtp_config()

    if not sender or not password:
        logger.warning(
            "Email credentials not configured (EMAIL_SENDER / EMAIL_PASSWORD). "
            "Skipping email send."
        )
        return False, "Email credentials not configured. Set EMAIL_SENDER and EMAIL_PASSWORD environment variables."

    try:
        msg = MIMEMultipart("mixed")
        msg["Subject"] = f"Your SEO Audit Report — {website_url} | ATI & AI"
        msg["From"] = f"ATI & AI SEO Audits <{sender}>"
        msg["To"] = to_email

        # HTML body
        html_body = _build_html_email(customer_name, website_url, seo_score, business_name)
        msg.attach(MIMEText(html_body, "html", "utf-8"))

        # PDF attachment
        if pdf_bytes:
            pdf_part = MIMEBase("application", "pdf")
            pdf_part.set_payload(pdf_bytes)
            encoders.encode_base64(pdf_part)
            pdf_part.add_header("Content-Disposition", 'attachment; filename="SEO_Audit_Report.pdf"')
            msg.attach(pdf_part)

        # HTML dashboard attachment
        if html_dashboard_content:
            html_part = MIMEBase("text", "html")
            html_part.set_payload(html_dashboard_content.encode("utf-8"))
            encoders.encode_base64(html_part)
            html_part.add_header("Content-Disposition", 'attachment; filename="SEO_Dashboard.html"')
            msg.attach(html_part)

        with smtplib.SMTP(smtp_host, smtp_port, timeout=30) as server:
            server.ehlo()
            server.starttls()
            server.login(sender, password)
            server.sendmail(sender, [to_email], msg.as_bytes())

        logger.info("Audit report email sent to %s", to_email)
        return True, f"Report successfully sent to {to_email}"

    except smtplib.SMTPAuthenticationError:
        msg_text = "SMTP authentication failed. Check EMAIL_SENDER and EMAIL_PASSWORD."
        logger.error(msg_text)
        return False, msg_text
    except smtplib.SMTPException as exc:
        msg_text = f"SMTP error: {exc}"
        logger.error(msg_text)
        return False, msg_text
    except Exception as exc:
        msg_text = f"Unexpected error sending email: {exc}"
        logger.error(msg_text, exc_info=True)
        return False, msg_text
