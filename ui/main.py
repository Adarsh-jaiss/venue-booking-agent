import streamlit as st
import requests
import json
import uuid
from datetime import datetime
from typing import Dict, List

# Import local modules
from config import API_BASE_URL, UI_TITLE, UI_LAYOUT

# Page configuration
st.set_page_config(
    page_title=UI_TITLE,
    page_icon="🏢",
    layout=UI_LAYOUT,
    initial_sidebar_state="collapsed"
)

# Clean CSS with proper positioning
st.markdown("""
<style>
/* Reset and base styles */
.stApp {
    background-color: #ffffff;
    color: #2c2c2c;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

/* Hide Streamlit elements */
#MainMenu, header, footer, .stDeployButton {
    visibility: hidden;
    display: none;
}

/* Fixed header */
.app-header {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    background: #ffffff;
    border-bottom: 1px solid #e0e0e0;
    z-index: 1000;
    padding: 1rem 2rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
    box-shadow: 0 2px 4px rgba(0,0,0,0.05);
}

.header-title {
    font-size: 1.8rem;
    font-weight: 600;
    color: #1a1a1a;
    margin: 0;
    line-height: 1;
}

.header-actions {
    display: flex;
    gap: 0.75rem;
    align-items: center;
}

.header-btn {
    background: #f8f9fa;
    border: 1px solid #e0e0e0;
    border-radius: 6px;
    color: #495057;
    padding: 0.5rem 1rem;
    font-weight: 500;
    font-size: 0.9rem;
    cursor: pointer;
    transition: all 0.2s ease;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

.header-btn:hover {
    background: #e9ecef;
    border-color: #adb5bd;
    color: #212529;
}

/* Main content with proper spacing */
.main-content {
    max-width: 900px;
    margin: 0 auto;
    padding: 0 1rem 120px 1rem;
    margin-top: 80px; /* Account for fixed header */
}

/* Messages */
.message {
    margin-bottom: 2rem;
    padding: 1.5rem;
    border-radius: 12px;
    line-height: 1.6;
    font-size: 1rem;
    background: transparent;
    border: 1px solid #e9ecef;
}

/* Venue cards */
.venue-card {
    background: #ffffff;
    border: 1px solid #e0e0e0;
    border-radius: 12px;
    padding: 2rem;
    margin: 1rem 0;
    transition: all 0.2s ease;
    box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}

.venue-card:hover {
    border-color: #4285f4;
    box-shadow: 0 4px 16px rgba(0,0,0,0.1);
    transform: translateY(-2px);
}

.venue-name {
    font-size: 1.4rem;
    font-weight: 600;
    color: #1a1a1a;
    margin-bottom: 0.8rem;
}

.venue-score {
    display: inline-block;
    padding: 0.4rem 1rem;
    border-radius: 20px;
    font-size: 0.9rem;
    font-weight: 500;
    margin-bottom: 1.2rem;
}

.score-excellent { background: #e8f5e9; color: #2e7d32; }
.score-good { background: #e3f2fd; color: #1976d2; }
.score-fair { background: #fff3e0; color: #f57c00; }
.score-poor { background: #ffebee; color: #d32f2f; }

.venue-details {
    display: grid;
    gap: 0.8rem;
    color: #555555;
    font-size: 1rem;
}

.venue-detail {
    display: flex;
    align-items: flex-start;
}

.detail-label {
    font-weight: 600;
    color: #333333;
    min-width: 100px;
    margin-right: 1rem;
}

/* Success message */
.success-message {
    background: #e8f5e9;
    border: 1px solid #c8e6c9;
    color: #2e7d32;
    padding: 1rem 1.5rem;
    border-radius: 8px;
    margin: 1.5rem 0;
    text-align: center;
    font-weight: 500;
}

/* Loading */
.loading-message {
    color: #666666;
    font-style: italic;
    padding: 0.5rem 0;
    font-size: 0.9rem;
}

.streaming-indicator {
    color: #4285f4;
    font-style: italic;
    font-size: 0.9rem;
    margin-bottom: 0.5rem;
}

.typing-cursor {
    color: #4285f4;
    animation: blink 1s infinite;
}

@keyframes blink {
    0%, 50% { opacity: 1; }
    51%, 100% { opacity: 0; }
}

/* Chat input styling */
.stChatInput {
    position: fixed;
    bottom: 0;
    left: 0;
    right: 0;
    background: #ffffff;
    border-top: 1px solid #e0e0e0;
    padding: 1rem;
    z-index: 1000;
}

.stChatInput > div {
    max-width: 900px;
    margin: 0 auto;
    background: #ffffff !important;
    border: 2px solid #e0e0e0 !important;
    border-radius: 12px !important;
    box-shadow: 0 2px 8px rgba(0,0,0,0.06) !important;
}

.stChatInput textarea {
    border: none !important;
    background: #ffffff !important;
    color: #2c2c2c !important;
    font-size: 1rem !important;
    padding: 1.2rem !important;
    line-height: 1.5 !important;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
}

.stChatInput textarea::placeholder {
    color: #888888 !important;
    opacity: 1 !important;
}

.stChatInput textarea:focus {
    outline: none !important;
    color: #2c2c2c !important;
    background: #ffffff !important;
}

.stChatInput > div:focus-within {
    border-color: #4285f4 !important;
    box-shadow: 0 0 0 3px rgba(66, 133, 244, 0.1) !important;
}

.stChatInput button {
    background: #4285f4 !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 8px !important;
    padding: 0.8rem 1.2rem !important;
    font-weight: 500 !important;
    transition: background 0.2s ease !important;
}

.stChatInput button:hover {
    background: #3367d6 !important;
}

/* Input text visibility fix */
.stChatInput input, .stChatInput textarea {
    color: #2c2c2c !important;
    -webkit-text-fill-color: #2c2c2c !important;
    opacity: 1 !important;
}

/* Streamlit buttons - hidden but functional */
.stButton {
    position: absolute;
    top: -9999px;
    left: -9999px;
    visibility: hidden;
}

/* Override any column display when buttons are present */
div[data-testid="column"]:has(.stButton) {
    display: none !important;
}

/* Content wrapper */
.content-wrapper {
    min-height: 60vh;
    padding: 2rem 0;
}

/* Grid layout for venues */
.venue-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
    gap: 1.5rem;
    margin: 2rem 0;
}

/* Responsive design */
@media (max-width: 768px) {
    .app-header {
    padding: 1rem;
    }
    
    .header-title {
        font-size: 1.5rem;
    }
    
    .header-actions {
    gap: 0.5rem;
    }
    
    .header-btn {
        padding: 0.4rem 0.8rem;
        font-size: 0.85rem;
    }
    
    .main-content {
        margin-top: 70px;
        padding: 0 0.5rem 120px 0.5rem;
    }
    
    .venue-grid {
        grid-template-columns: 1fr;
    }
}
</style>
""", unsafe_allow_html=True)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if "user_id" not in st.session_state:
    st.session_state.user_id = str(uuid.uuid4())
if "organization_id" not in st.session_state:
    st.session_state.organization_id = "default_org"
if "is_streaming" not in st.session_state:
    st.session_state.is_streaming = False

def parse_venue_results(content: str) -> List[Dict]:
    """Parse venue results from the agent response"""
    venues = []
    try:
        # Try to parse JSON content
        if content.strip().startswith('[') or content.strip().startswith('{'):
            try:
                parsed_json = json.loads(content)
                if isinstance(parsed_json, list):
                    venues = [item for item in parsed_json if isinstance(item, dict)]
                elif isinstance(parsed_json, dict):
                    venues = [parsed_json]
                return venues
            except json.JSONDecodeError:
                pass
        
        # Extract venue data from text
            lines = content.split('\n')
            current_venue = {}
            for line in lines:
                            line = line.strip()
            if any(keyword in line.lower() for keyword in ['business:', 'name:', 'venue:']):
                if current_venue:
                    venues.append(current_venue)
                current_venue = {'name': line.split(':', 1)[1].strip() if ':' in line else line}
            elif ':' in line and current_venue:
                key, value = line.split(':', 1)
                key = key.strip().lower()
                value = value.strip()
                if key in ['location', 'type', 'capacity', 'rating', 'phone', 'email']:
                    current_venue[key] = value
                elif key == 'score':
                    try:
                        current_venue['score'] = float(value.split()[0])
                    except:
                        pass
            if current_venue:
                venues.append(current_venue)
    except Exception:
        pass
    return venues

def display_venue_card(venue: Dict):
    """Display a clean venue card"""
    metadata = venue.get('metadata', {})
    score = venue.get('score', 0.0)
    
    # Extract information
    name = metadata.get('business_name', venue.get('name', 'Venue'))
    location = f"{metadata.get('city', '')}, {metadata.get('state', '')}".strip(', ')
    venue_type = metadata.get('vendor_type', venue.get('type', ''))
    description = metadata.get('business_description', venue.get('description', ''))
    rating = metadata.get('average_rating', venue.get('rating', ''))
    capacity = metadata.get('capacity', venue.get('capacity', ''))
    phone = metadata.get('phone', venue.get('phone', ''))
    email = metadata.get('email', venue.get('email', ''))
    
    # Score styling
    if score >= 0.9:
        score_class = "score-excellent"
    elif score >= 0.8:
        score_class = "score-good"
    elif score >= 0.7:
        score_class = "score-fair"
    else:
        score_class = "score-poor"
    
    details = []
    if location: details.append(f'<div class="venue-detail"><span class="detail-label">Location:</span>{location}</div>')
    if venue_type: details.append(f'<div class="venue-detail"><span class="detail-label">Type:</span>{venue_type}</div>')
    if rating: details.append(f'<div class="venue-detail"><span class="detail-label">Rating:</span>{rating}</div>')
    if capacity: details.append(f'<div class="venue-detail"><span class="detail-label">Capacity:</span>{capacity}</div>')
    if phone: details.append(f'<div class="venue-detail"><span class="detail-label">Phone:</span>{phone}</div>')
    if email: details.append(f'<div class="venue-detail"><span class="detail-label">Email:</span>{email}</div>')
    
    venue_html = f"""
    <div class="venue-card">
        <div class="venue-name">{name}</div>
        <div class="venue-score {score_class}">Match Score: {score:.2f}</div>
        <div class="venue-details">
            {''.join(details)}
        </div>
        {f'<div style="margin-top: 1rem; color: #666; font-style: italic;">{description}</div>' if description else ''}
    </div>
    """
    return venue_html

def stream_agent_response(prompt: str, streaming_container):
    """Stream response from agent with proper text flow visibility"""
    try:
        payload = {
            "session": st.session_state.session_id,
            "user_id": st.session_state.user_id,
            "prompt": prompt,
            "organization_id": st.session_state.organization_id
        }
        
        response = requests.post(
            f"{API_BASE_URL}/stream",
            json=payload,
            stream=True,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code != 200:
            streaming_container.error(f"Error: {response.status_code}")
            return
        
        st.session_state.is_streaming = True
        current_response = ""
        
        # Show initial loading state
        streaming_container.markdown(
            '<div class="message"><div class="loading-message">Agent is thinking...</div></div>', 
            unsafe_allow_html=True
        )
        
        for line in response.iter_lines():
            if line:
                line_str = line.decode('utf-8')
                if line_str.startswith('data: '):
                    try:
                        chunk_data = json.loads(line_str[6:])
                        category = chunk_data.get('category')
                        content = chunk_data.get('content', '')
                        
                        if category == 'text.chunk' and content:
                            current_response += str(content)
                            # Show streaming text with typing indicator
                            streaming_container.markdown(f'''
                            <div class="message">
                                <div class="streaming-indicator">Assistant is typing...</div>
                                <div style="margin-top: 0.5rem;">{current_response}<span class="typing-cursor">|</span></div>
                            </div>
                            ''', unsafe_allow_html=True)
                    except json.JSONDecodeError:
                        continue
        
        st.session_state.is_streaming = False
        
        # Parse venues
        venues = parse_venue_results(current_response)
        
        # Display final response without typing indicator
        final_html = f'<div class="message">{current_response}</div>'
        
        if venues:
            final_html += f'<div class="success-message">Found {len(venues)} venue recommendations</div>'
            venue_cards = [display_venue_card(venue) for venue in venues]
            final_html += f'<div class="venue-grid">{"".join(venue_cards)}</div>'
        
        streaming_container.markdown(final_html, unsafe_allow_html=True)
        
        # Save to history
        st.session_state.messages.append({
            "role": "assistant",
            "content": current_response,
            "venues": venues,
            "timestamp": datetime.now()
        })
        
    except Exception as e:
        streaming_container.error(f"Error: {e}")
        st.session_state.is_streaming = False

def display_message(message: Dict):
    """Display a message"""
    content = message["content"]
    venues = message.get("venues", [])
    
    st.markdown(f'<div class="message">{content}</div>', unsafe_allow_html=True)
    
    if venues:
        st.markdown(f'<div class="success-message">Found {len(venues)} venue recommendations</div>', unsafe_allow_html=True)
        venue_cards = [display_venue_card(venue) for venue in venues]
        st.markdown(f'<div class="venue-grid">{"".join(venue_cards)}</div>', unsafe_allow_html=True)

# Create the fixed header using HTML and CSS
st.markdown("""
<div class="app-header">
    <div class="header-title">Venue Booking Assistant</div>
    <div class="header-actions" id="header-actions">
        <!-- Buttons will be positioned here by Streamlit -->
    </div>
</div>
""", unsafe_allow_html=True)

# Position buttons in the header using custom CSS positioning
st.markdown("""
<style>
/* Position the button container in the header */
.stButton {
    position: fixed !important;
    top: 1rem !important;
    right: 2rem !important;
    z-index: 1001 !important;
    visibility: visible !important;
    display: inline-block !important;
}

/* Style the buttons to match header design */
.stButton > button {
    background: #f8f9fa !important;
    border: 1px solid #e0e0e0 !important;
    border-radius: 6px !important;
    color: #495057 !important;
    padding: 0.5rem 1rem !important;
    font-weight: 500 !important;
    font-size: 0.9rem !important;
    margin-left: 0.75rem !important;
    transition: all 0.2s ease !important;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
}

.stButton > button:hover {
    background: #e9ecef !important;
    border-color: #adb5bd !important;
    color: #212529 !important;
}

/* Override column display for header buttons */
div[data-testid="column"] {
    position: fixed !important;
    top: 1rem !important;
    right: 2rem !important;
    z-index: 1001 !important;
    display: flex !important;
    gap: 0.75rem !important;
    background: transparent !important;
}
</style>
""", unsafe_allow_html=True)

# Functional buttons that will be positioned in the header
col1, col2 = st.columns([1, 1])
with col1:
    if st.button("New Session", key="new_session", help="Start a new conversation"):
        st.session_state.session_id = str(uuid.uuid4())
        st.session_state.messages = []
        st.rerun()
        
with col2:
    if st.button("Clear Chat", key="clear_chat", help="Clear conversation history"):
        st.session_state.messages = []
        st.rerun()
    
# Main content area with proper container
st.markdown('<div class="main-content">', unsafe_allow_html=True)

# Add a content wrapper for better spacing
st.markdown('<div class="content-wrapper">', unsafe_allow_html=True)

# Chat history
for message in st.session_state.messages:
    display_message(message)

st.markdown('</div>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# Chat input
if not st.session_state.is_streaming:
    prompt = st.chat_input("Describe your event and venue requirements...")
    
    if prompt:
        # Add user message to history immediately
        st.session_state.messages.append({
            "role": "user",
            "content": prompt,
            "timestamp": datetime.now()
        })
        
        # Display user message immediately
        st.markdown(f'<div class="message">{prompt}</div>', unsafe_allow_html=True)
        
        # Create container for streaming response at the top
        streaming_container = st.empty()
        
        # Stream response
        stream_agent_response(prompt, streaming_container)
        
        st.rerun()
else:
    st.markdown('<div class="loading-message">Processing your request...</div>', unsafe_allow_html=True)