"""
Security Utilities
===================
Input validation, PII filtering, and other security functions.
"""

import re
from typing import Any, Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


# =============================================================================
# Input Validation
# =============================================================================

def sanitize_input(text: str) -> str:
    """
    Basic input sanitization.
    Remove potential injection patterns.
    """
    if not text:
        return ""
    
    # Remove null bytes
    text = text.replace('\x00', '')
    
    # Limit length
    max_length = 10000
    if len(text) > max_length:
        text = text[:max_length]
        logger.warning(f"Input truncated to {max_length} characters")
    
    return text


def validate_email(email: str) -> bool:
    """Validate email format."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_url(url: str) -> bool:
    """Validate URL format."""
    pattern = r'^https?://[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}.*$'
    return bool(re.match(pattern, url))


# =============================================================================
# Prompt Injection Detection
# =============================================================================

INJECTION_PATTERNS = [
    r'ignore\s+(previous|above|all)\s+instructions',
    r'disregard\s+(previous|above|all)',
    r'forget\s+(everything|all)',
    r'new\s+instructions',
    r'override\s+instructions',
    r'system\s*:\s*',
    r'<\|.*\|>',
    r'\[\[.*\]\]',
    r'```system',
]


def detect_prompt_injection(text: str) -> Tuple[bool, Optional[str]]:
    """
    Detect potential prompt injection attempts.
    
    Returns:
        (is_safe, detected_pattern or None)
    """
    if not text:
        return True, None
    
    text_lower = text.lower()
    
    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, text_lower):
            logger.warning(f"Potential prompt injection detected: {pattern}")
            return False, pattern
    
    return True, None


# =============================================================================
# PII Detection and Filtering
# =============================================================================

PII_PATTERNS = {
    'ssn': r'\b\d{3}-\d{2}-\d{4}\b',
    'credit_card': r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b',
    'phone': r'\b\d{3}[\s.-]?\d{3}[\s.-]?\d{4}\b',
    'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
    'ip_address': r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b',
}


def detect_pii(text: str) -> Dict[str, List[str]]:
    """
    Detect PII in text.
    
    Returns:
        Dict of PII type -> list of matches
    """
    if not text:
        return {}
    
    found = {}
    for pii_type, pattern in PII_PATTERNS.items():
        matches = re.findall(pattern, text)
        if matches:
            found[pii_type] = matches
            logger.info(f"Detected {len(matches)} {pii_type} instance(s)")
    
    return found


def redact_pii(text: str, pii_types: Optional[List[str]] = None) -> str:
    """
    Redact PII from text.
    
    Args:
        text: Input text
        pii_types: List of PII types to redact (default: all)
        
    Returns:
        Text with PII redacted
    """
    if not text:
        return ""
    
    types_to_redact = pii_types or list(PII_PATTERNS.keys())
    
    result = text
    for pii_type in types_to_redact:
        if pii_type in PII_PATTERNS:
            pattern = PII_PATTERNS[pii_type]
            result = re.sub(pattern, f'[REDACTED-{pii_type.upper()}]', result)
    
    return result


# =============================================================================
# Secret Detection
# =============================================================================

SECRET_PATTERNS = [
    (r'["\']?[a-zA-Z_]*api[_-]?key["\']?\s*[=:]\s*["\'][a-zA-Z0-9_-]{20,}["\']', 'API Key'),
    (r'["\']?[a-zA-Z_]*secret[_-]?key["\']?\s*[=:]\s*["\'][a-zA-Z0-9_-]{20,}["\']', 'Secret Key'),
    (r'["\']?password["\']?\s*[=:]\s*["\'][^"\']{8,}["\']', 'Password'),
    (r'["\']?token["\']?\s*[=:]\s*["\'][a-zA-Z0-9_-]{20,}["\']', 'Token'),
    (r'sk-[a-zA-Z0-9]{48}', 'OpenAI Key'),
    (r'sk_live_[a-zA-Z0-9]{24,}', 'Stripe Key'),
    (r'AKIA[0-9A-Z]{16}', 'AWS Key'),
]


def detect_secrets(text: str) -> List[Dict[str, str]]:
    """
    Detect hardcoded secrets in text/code.
    
    Returns:
        List of detected secrets with type
    """
    if not text:
        return []
    
    secrets = []
    for pattern, secret_type in SECRET_PATTERNS:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            secrets.append({
                'type': secret_type,
                'pattern': pattern,
                'match': match[:20] + '...' if len(match) > 20 else match
            })
            logger.warning(f"Detected potential {secret_type} in input")
    
    return secrets


# =============================================================================
# Rate Limiting Helper
# =============================================================================

class RateLimiter:
    """Simple in-memory rate limiter."""
    
    def __init__(self, max_requests: int, window_seconds: int):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: Dict[str, List[float]] = {}
    
    def is_allowed(self, key: str) -> bool:
        """Check if request is allowed for key."""
        import time
        now = time.time()
        
        if key not in self.requests:
            self.requests[key] = []
        
        # Remove old requests
        self.requests[key] = [
            t for t in self.requests[key]
            if now - t < self.window_seconds
        ]
        
        # Check limit
        if len(self.requests[key]) >= self.max_requests:
            return False
        
        # Record request
        self.requests[key].append(now)
        return True


# =============================================================================
# Content Safety Check
# =============================================================================

UNSAFE_CONTENT_PATTERNS = [
    r'\b(kill|murder|harm|attack)\s+(yourself|someone|people)\b',
    r'\b(how\s+to\s+make|create|build)\s+(bomb|weapon|drug)\b',
    r'\b(illegal|illicit)\s+(activity|activities|drugs)\b',
]


def check_content_safety(text: str) -> Tuple[bool, Optional[str]]:
    """
    Check if content is safe.
    
    Returns:
        (is_safe, detected_issue or None)
    """
    if not text:
        return True, None
    
    text_lower = text.lower()
    
    for pattern in UNSAFE_CONTENT_PATTERNS:
        if re.search(pattern, text_lower):
            logger.warning(f"Unsafe content detected: {pattern}")
            return False, f"Content flagged: {pattern[:30]}..."
    
    return True, None
