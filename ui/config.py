import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API Configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
API_TIMEOUT = int(os.getenv("API_TIMEOUT", "30"))

# UI Configuration
UI_TITLE = "Venue Booking Assistant"
UI_ICON = "VBA"
UI_LAYOUT = "wide"

# Session Configuration
DEFAULT_SESSION_TIMEOUT = 3600  # 1 hour in seconds
MAX_MESSAGES_IN_HISTORY = 50

# Venue Display Configuration
MAX_VENUES_PER_ROW = 2
MAX_REASONING_STEPS_DISPLAY = 5

# Styling Configuration
COLORS = {
    "primary": "#1976d2",
    "secondary": "#9c27b0", 
    "success": "#4caf50",
    "warning": "#ff9800",
    "error": "#d32f2f",
    "info": "#2196f3"
}

# Example prompts for quick testing
EXAMPLE_PROMPTS = [
    "I need a venue for a wedding in Boston for 150 guests",
    "Find me a corporate event space in New York with A/V equipment", 
    "Looking for a birthday party venue in San Francisco",
    "I need a venue for a conference with 300 attendees",
    "Find me an outdoor wedding venue in California for 200 guests",
    "I need a hotel ballroom in Chicago for a gala dinner"
] 