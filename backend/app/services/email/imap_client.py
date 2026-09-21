import imaplib
import email
from email.header import decode_header
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, List, Dict, Any
from app.services.email.base import BaseEmailClient, EmailMessage

class IMAPEmailClient(BaseEmailClient):
    """
    Standard IMAP/SMTP client supporting Gmail (App Password), Outlook/Office 365,
    iCloud, or any standard local/remote IMAP mail server.
    """

    def __init__(
        self,
        host: str,
        port: int = 993,
        username: str = "",
        password: str = "",
        use_ssl: bool = True,
        smtp_host: Optional[str] = None,
        smtp_port: int = 587
    ):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.use_ssl = use_ssl
        self.smtp_host = smtp_host or host.replace("imap", "smtp")
        self.smtp_port = smtp_port

    @property
    def provider_name(self) -> str:
        return "imap"

    def _get_connection(self) -> imaplib.IMAP4:
        if self.use_ssl:
            conn = imaplib.IMAP4_SSL(self.host, self.port)
        else:
            conn = imaplib.IMAP4(self.host, self.port)
        conn.login(self.username, self.password)
        return conn

    def _decode_header_str(self, header_raw: Optional[str]) -> str:
        if not header_raw:
            return ""
        decoded_parts = decode_header(header_raw)
        result = []
        for content, encoding in decoded_parts:
            if isinstance(content, bytes):
                try:
                    result.append(content.decode(encoding or "utf-8", errors="replace"))
                except Exception:
                    result.append(content.decode("latin-1", errors="replace"))
            else:
                result.append(str(content))
        return "".join(result)

    def _parse_email_message(self, num_id: str, raw_email_bytes: bytes, status: str = "unread") -> EmailMessage:
        msg = email.message_from_bytes(raw_email_bytes)
        subject = self._decode_header_str(msg.get("Subject", "Sin Asunto"))
        sender = self._decode_header_str(msg.get("From", "Remitente Desconocido"))
        recipient = self._decode_header_str(msg.get("To", self.username))
        date_str = self._decode_header_str(msg.get("Date", "Fecha Desconocida"))

        body = ""
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition"))
                if content_type == "text/plain" and "attachment" not in content_disposition:
                    payload = part.get_payload(decode=True)
                    if payload:
                        charset = part.get_content_charset() or "utf-8"
                        body = payload.decode(charset, errors="replace")
                        break
        else:
            payload = msg.get_payload(decode=True)
            if payload:
                charset = msg.get_content_charset() or "utf-8"
                body = payload.decode(charset, errors="replace")

        clean_body = body.strip()
        snippet = clean_body[:120] + "..." if len(clean_body) > 120 else clean_body

        is_important = any(kw in (subject + sender).lower() for kw in ["urgente", "importante", "decano", "director", "banco", "alerta"])
        priority = "HIGH" if is_important else "MEDIUM"

        return EmailMessage(
            id=str(num_id),
            sender=sender,
            recipient=recipient,
            subject=subject,
            body=clean_body or snippet,
            snippet=snippet,
            status="unread" if status == "unread" else "read",
            category="work" if is_important else "general",
            received_at=date_str,
            is_important=is_important,
            priority=priority
        )

    async def list_unread(self, limit: int = 10) -> List[EmailMessage]:
        conn = self._get_connection()
        try:
            conn.select("INBOX")
            status, response = conn.search(None, "UNSEEN")
            if status != "OK" or not response or not response[0]:
                return []
            
            message_ids = response[0].split()
            message_ids.reverse()  # most recent first
            results = []
            for num in message_ids[:limit]:
                num_str = num.decode("utf-8")
                res, data = conn.fetch(num, "(RFC822)")
                if res == "OK" and data and isinstance(data[0], tuple):
                    results.append(self._parse_email_message(num_str, data[0][1], status="unread"))
            return results
        finally:
            try:
                conn.close()
                conn.logout()
            except Exception:
                pass

    async def list_all(self, status: Optional[str] = None, limit: int = 10) -> List[EmailMessage]:
        if status == "unread":
            return await self.list_unread(limit=limit)
        
        conn = self._get_connection()
        try:
            conn.select("INBOX")
            status_code, response = conn.search(None, "ALL")
            if status_code != "OK" or not response or not response[0]:
                return []
            
            message_ids = response[0].split()
            message_ids.reverse()
            results = []
            for num in message_ids[:limit]:
                num_str = num.decode("utf-8")
                res, data = conn.fetch(num, "(RFC822)")
                if res == "OK" and data and isinstance(data[0], tuple):
                    results.append(self._parse_email_message(num_str, data[0][1], status="read"))
            return results
        finally:
            try:
                conn.close()
                conn.logout()
            except Exception:
                pass

    async def get_by_id(self, email_id: str) -> Optional[EmailMessage]:
        conn = self._get_connection()
        try:
            conn.select("INBOX")
            res, data = conn.fetch(email_id.encode("utf-8"), "(RFC822)")
            if res == "OK" and data and isinstance(data[0], tuple):
                return self._parse_email_message(email_id, data[0][1], status="read")
            return None
        finally:
            try:
                conn.close()
                conn.logout()
            except Exception:
                pass

    async def search(self, query: str, limit: int = 10) -> List[EmailMessage]:
        conn = self._get_connection()
        try:
            conn.select("INBOX")
            clean_q = query.strip()
            # Search subject or from
            search_crit = f'(OR FROM "{clean_q}" SUBJECT "{clean_q}")'
            status, response = conn.search(None, search_crit)
            if status != "OK" or not response or not response[0]:
                # Fallback to ALL and filter client-side
                status, response = conn.search(None, "ALL")
                if status != "OK" or not response or not response[0]:
                    return []

            message_ids = response[0].split()
            message_ids.reverse()
            results = []
            for num in message_ids[:limit]:
                num_str = num.decode("utf-8")
                res, data = conn.fetch(num, "(RFC822)")
                if res == "OK" and data and isinstance(data[0], tuple):
                    parsed = self._parse_email_message(num_str, data[0][1], status="read")
                    if clean_q.lower() in (parsed.sender + parsed.subject + parsed.body).lower():
                        results.append(parsed)
            return results
        finally:
            try:
                conn.close()
                conn.logout()
            except Exception:
                pass

    async def create_draft(self, recipient: str, subject: str, body: str) -> EmailMessage:
        # In IMAP, drafts are saved into the "[Gmail]/Drafts" or "Drafts" folder
        import uuid
        from datetime import datetime
        draft_msg = EmailMessage(
            id=str(uuid.uuid4()),
            sender=self.username or "usuario@asistente.ai",
            recipient=recipient,
            subject=f"[Borrador] {subject}",
            body=body,
            snippet=body[:100],
            status="draft",
            category="work",
            received_at=datetime.now().strftime("%Y-%m-%d %H:%M"),
            is_important=False,
            priority="MEDIUM"
        )
        return draft_msg

    async def send_email(self, recipient: str, subject: str, body: str) -> bool:
        """
        Sends email through SMTP (only invoked when user has explicitly confirmed).
        """
        msg = MIMEMultipart()
        msg["From"] = self.username
        msg["To"] = recipient
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
            server.starttls()
            server.login(self.username, self.password)
            server.send_message(msg)
        return True
