import json
import re
from typing import Dict, List, Any, Optional
from datetime import datetime
import streamlit as st

def format_timestamp(timestamp: datetime) -> str:
    """Format timestamp for display"""
    return timestamp.strftime("%H:%M:%S")

def sanitize_html(text: str) -> str:
    """Sanitize text for safe HTML display"""
    if not isinstance(text, str):
        return str(text)
    
    # Replace newlines with HTML breaks
    text = text.replace('\n', '<br>')
    # Basic HTML escaping
    text = text.replace('&', '&amp;')
    text = text.replace('<', '&lt;')
    text = text.replace('>', '&gt;')
    text = text.replace('"', '&quot;')
    text = text.replace("'", '&#x27;')
    
    return text

def extract_json_from_text(text: str) -> Optional[Dict]:
    """Extract JSON objects from text content"""
    try:
        # Look for JSON blocks in the text
        json_pattern = r'\{.*?\}'
        matches = re.findall(json_pattern, text, re.DOTALL)
        
        for match in matches:
            try:
                return json.loads(match)
            except json.JSONDecodeError:
                continue
        
        return None
    except Exception:
        return None

def parse_venue_metadata(venue: Dict) -> Dict[str, str]:
    """Parse and format venue metadata for display"""
    metadata = venue.get('metadata', {})
    
    parsed = {
        'name': metadata.get('business_name', venue.get('name', 'Unknown Venue')),
        'location': f"{metadata.get('city', '')}, {metadata.get('state', '')}".strip(', '),
        'type': metadata.get('vendor_type', metadata.get('venue_type', '')),
        'description': metadata.get('business_description', '')[:200] + ('...' if len(metadata.get('business_description', '')) > 200 else ''),
        'rating': metadata.get('average_rating', ''),
        'capacity': metadata.get('capacity', metadata.get('number_of_guests', '')),
        'phone': metadata.get('phone', ''),
        'email': metadata.get('email', ''),
        'website': metadata.get('website', ''),
        'score': venue.get('score', 0.0)
    }
    
    # Parse event types
    event_types = metadata.get('event_types', '')
    if isinstance(event_types, str) and event_types:
        parsed['event_types'] = [et.strip() for et in event_types.split(',') if et.strip()]
    else:
        parsed['event_types'] = []
    
    # Parse languages
    languages = metadata.get('languages', '')
    if isinstance(languages, str) and languages:
        parsed['languages'] = [lang.strip() for lang in languages.split(',') if lang.strip()]
    else:
        parsed['languages'] = []
    
    return parsed

def format_venue_score(score: float) -> str:
    """Format venue score for display"""
    if score >= 0.9:
        return f"{score:.2f} (Excellent Match)"
    elif score >= 0.8:
        return f"{score:.2f} (Good Match)"
    elif score >= 0.7:
        return f"{score:.2f} (Fair Match)"
    else:
        return f"{score:.2f} (Partial Match)"

def create_venue_summary(venues: List[Dict]) -> str:
    """Create a summary of venue search results"""
    if not venues:
        return "No venues found matching your criteria."
    
    total = len(venues)
    high_score = sum(1 for v in venues if v.get('score', 0) >= 0.8)
    
    summary = f"Found {total} venue{'s' if total != 1 else ''}"
    if high_score > 0:
        summary += f" ({high_score} high-quality match{'es' if high_score != 1 else ''})"
    
    return summary

def validate_api_response(response_data: Dict) -> bool:
    """Validate API response structure"""
    required_fields = ['type', 'category']
    return all(field in response_data for field in required_fields)

def extract_tool_info(content: Any) -> Dict[str, str]:
    """Extract tool information from streaming content"""
    if not isinstance(content, dict):
        return {'name': 'Unknown Tool', 'content': str(content)}
    
    return {
        'name': content.get('name', 'Unknown Tool'),
        'content': str(content.get('content', '')),
        'args': str(content.get('args', '')) if content.get('args') else ''
    }

def truncate_text(text: str, max_length: int = 100) -> str:
    """Truncate text to specified length with ellipsis"""
    if len(text) <= max_length:
        return text
    return text[:max_length-3] + "..."

def format_currency(amount: str) -> str:
    """Format currency amounts for display"""
    if not amount or amount == '':
        return ''
    
    try:
        # Try to parse as number
        num = float(amount.replace('$', '').replace(',', ''))
        return f"${num:,.0f}"
    except ValueError:
        return amount

def get_venue_type_icon(venue_type: str) -> str:
    """Get appropriate label for venue type"""
    venue_type = venue_type.lower()
    
    labels = {
        'hotel': 'Hotel',
        'restaurant': 'Restaurant',
        'banquet': 'Banquet',
        'outdoor': 'Outdoor',
        'conference': 'Conference',
        'wedding': 'Wedding',
        'ballroom': 'Ballroom',
        'garden': 'Garden',
        'rooftop': 'Rooftop',
        'beach': 'Beach',
        'farm': 'Farm',
        'museum': 'Museum',
        'gallery': 'Gallery'
    }
    
    for key, label in labels.items():
        if key in venue_type:
            return label
    
    return 'Venue'  # Default label

def calculate_venue_compatibility(venue: Dict, user_requirements: Dict) -> float:
    """Calculate compatibility score between venue and user requirements"""
    # This is a simplified compatibility calculation
    # In a real implementation, this would be more sophisticated
    
    score = 0.0
    total_factors = 0
    
    # Location matching
    venue_location = venue.get('metadata', {}).get('city', '').lower()
    required_location = user_requirements.get('location', '').lower()
    if venue_location and required_location and required_location in venue_location:
        score += 0.3
    total_factors += 0.3
    
    # Capacity matching
    venue_capacity = venue.get('metadata', {}).get('capacity', '')
    required_guests = user_requirements.get('guests', 0)
    if venue_capacity and required_guests:
        try:
            capacity = int(venue_capacity)
            if capacity >= required_guests * 0.8 and capacity <= required_guests * 1.5:
                score += 0.3
        except ValueError:
            pass
    total_factors += 0.3
    
    # Event type matching
    venue_event_types = venue.get('metadata', {}).get('event_types', '').lower()
    required_event_type = user_requirements.get('event_type', '').lower()
    if venue_event_types and required_event_type and required_event_type in venue_event_types:
        score += 0.2
    total_factors += 0.2
    
    # Rating bonus
    venue_rating = venue.get('metadata', {}).get('average_rating', '')
    if venue_rating:
        try:
            rating = float(venue_rating)
            if rating >= 4.0:
                score += 0.2
        except ValueError:
            pass
    total_factors += 0.2
    
    return score / total_factors if total_factors > 0 else 0.0 