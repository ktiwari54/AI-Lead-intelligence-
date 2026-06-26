from celery import shared_task
from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)


@shared_task(bind=True, max_retries=3, name="notifications.send_email")
def send_email_task(self, to: str, subject: str, body: str, html_body: str | None = None):
    logger.info(f"Sending email to {to}: {subject}")
    try:
        from backend.config import settings
        import smtplib
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText

        msg = MIMEMultipart("alternative")
        msg["From"] = settings.FROM_EMAIL
        msg["To"] = to
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))
        if html_body:
            msg.attach(MIMEText(html_body, "html"))

        if settings.SMTP_HOST:
            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
                server.starttls()
                if settings.SMTP_USER:
                    server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                server.send_message(msg)
        logger.info(f"Email sent to {to}")
        return {"status": "sent", "to": to}
    except Exception as exc:
        logger.error(f"Failed to send email to {to}: {exc}")
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, name="notifications.send_webhook")
def send_webhook_task(self, url: str, payload: dict, headers: dict | None = None):
    logger.info(f"Sending webhook to {url}")
    try:
        import httpx
        from tenacity import retry, stop_after_attempt, wait_exponential
        with httpx.Client(timeout=30) as client:
            response = client.post(url, json=payload, headers=headers or {})
            response.raise_for_status()
        return {"status": "sent", "url": url, "http_status": response.status_code}
    except Exception as exc:
        logger.error(f"Webhook delivery failed: {exc}")
        raise self.retry(exc=exc)
