"""Central input validation."""
import re
from datetime import date

def required(value, label):
    value = str(value or '').strip()
    if not value:
        raise ValueError(f'{label} is required.')
    return value

def email(value):
    value = str(value or '').strip()
    if value and not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+', value):
        raise ValueError('Enter a valid email address.')
    return value

def year(value):
    if value in ('', None): return None
    try: result = int(value)
    except (ValueError, TypeError): raise ValueError('Publication year must be a number.')
    if result < 1000 or result > date.today().year + 1: raise ValueError('Publication year is out of range.')
    return result

def quantity(value):
    try: result = int(value)
    except (ValueError, TypeError): raise ValueError('Copies must be a whole number.')
    if result < 0: raise ValueError('Copies cannot be negative.')
    return result

