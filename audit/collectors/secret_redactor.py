import re

SECRET_PATTERNS = [
    # AWS Keys
    (re.compile(r'(?i)(aws_access_key_id|aws_secret_access_key)\s*[=:]\s*[\'"]?([A-Za-z0-9/+=]+)[\'"]?'), r'\1 = [REDACTED]'),
    # Bearer Tokens
    (re.compile(r'(?i)(bearer\s+)([A-Za-z0-9\-\._~\+\/]+=*)'), r'\1[REDACTED]'),
    # Passwords
    (re.compile(r'(?i)(password\s*[=:]\s*)[\'"]?([^\s\'"]+)[\'"]?'), r'\1[REDACTED]'),
    # Connection strings
    (re.compile(r'(?i)(mysql|postgresql|postgres|mongodb)(\+.*?://)(.*?:)(.*?)@'), r'\1\2\3[REDACTED]@'),
]

def redact_secrets(text: str) -> str:
    """Redacts common secrets from the provided text."""
    if not text:
        return text
    
    redacted_text = text
    for pattern, replacement in SECRET_PATTERNS:
        redacted_text = pattern.sub(replacement, redacted_text)
    
    return redacted_text
