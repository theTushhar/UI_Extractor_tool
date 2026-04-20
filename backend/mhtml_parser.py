import email
import quopri
import re

def is_mhtml(content: str) -> bool:
    """
    Checks if the content looks like an MHTML archive.
    """
    # MHTML typically starts with MIME headers
    if "MIME-Version:" in content and "multipart/related" in content:
        return True
    # Look for common MHTML boundary or Blink snapshot headers
    if "Snapshot-Content-Location:" in content or "From: <Saved by Blink>" in content:
        return True
    return False

def clean_mhtml_to_html(content: str) -> str:
    """
    Parses an MHTML string and returns the primary HTML content part.
    If it's not MHTML, it returns the content as-is.
    """
    if not is_mhtml(content):
        return content

    try:
        # The email module works best with bytes for parsing complex MIME
        msg = email.message_from_string(content)
        
        if not msg.is_multipart():
            # If for some reason it's not multipart but encoded
            payload = msg.get_payload(decode=True)
            if payload:
                return payload.decode('utf-8', errors='replace')
            return content

        # Look for the text/html part
        for part in msg.walk():
            content_type = part.get_content_type()
            if content_type == "text/html":
                payload = part.get_payload(decode=True)
                if payload:
                    # Some MHTML might use different charsets
                    charset = part.get_content_charset() or 'utf-8'
                    try:
                        return payload.decode(charset, errors='replace')
                    except LookupError:
                        return payload.decode('utf-8', errors='replace')
        
        return content
    except Exception as e:
        # Fallback to a regex-based extraction if email module fails
        # (Though email module is usually robust for MHTML)
        print(f"MHTML parsing error: {e}")
        return content
