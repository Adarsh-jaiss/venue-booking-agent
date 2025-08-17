
def safe_get(obj, key, default=None):
    """Safely get value from object with default fallback"""
    if obj is None:
        return default
    if isinstance(obj, dict):
        return obj.get(key, default)
    return default

def safe_str(value, max_length=None):
    """Safely convert value to string with optional truncation"""
    if value is None:
        return ""
    str_val = str(value).strip()
    if max_length and len(str_val) > max_length:
        return str_val[:max_length] + "..."
    return str_val

def safe_int(value, default=0):
    """Safely convert value to int with default"""
    if value is None:
        return default
    try:
        return int(value)
    except (ValueError, TypeError):
        return default

def safe_float(value, default=0.0):
    """Safely convert value to float with default"""
    if value is None:
        return default
    try:
        return float(value)
    except (ValueError, TypeError):
        return default

def safe_bool(value, default=False):
    """Safely convert value to boolean with default"""
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in ('true', '1', 'yes', 'on')
    try:
        return bool(value)
    except (ValueError, TypeError):
        return default

def safe_list(value, default=None):
    """Safely convert value to list with default"""
    if default is None:
        default = []
    if value is None:
        return default
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        # Handle comma-separated strings
        return [item.strip() for item in value.split(',') if item.strip()]
    try:
        return list(value)
    except (ValueError, TypeError):
        return default

