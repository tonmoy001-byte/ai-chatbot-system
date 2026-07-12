import re
from typing import Optional


def validate_phone(phone: str) -> bool:
    """Validate phone number format."""
    pattern = r'^\+?1?\d{9,15}$'
    return bool(re.match(pattern, phone))


def validate_email(email: str) -> bool:
    """Validate email format."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_order_number(order_number: str) -> bool:
    """Validate order number format."""
    pattern = r'^ORD-\d{6,}$'
    return bool(re.match(pattern, order_number))


def sanitize_input(text: str) -> str:
    """Sanitize user input."""
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    # Remove potentially dangerous characters
    text = re.sub(r'[<>"\']', '', text)
    return text.strip()


def format_currency(amount: float, currency: str = "USD") -> str:
    """Format amount as currency string."""
    if currency == "USD":
        return f"${amount:.2f}"
    elif currency == "EUR":
        return f"€{amount:.2f}"
    elif currency == "GBP":
        return f"£{amount:.2f}"
    else:
        return f"{amount:.2f} {currency}"
