# Venue Booking Assistant - Streamlit UI

This directory contains the Streamlit web interface for the Venue Booking Assistant. The UI provides a chat-based interface to interact with the AI agent and view venue recommendations.

## Features

### 🚀 Real-time Streaming
- **Live Agent Responses**: See the agent's responses as they're generated
- **Reasoning Display**: Watch the agent's thinking process in real-time
- **Tool Execution Tracking**: Monitor when the agent uses tools like venue search

### 🏨 Venue Display
- **Rich Venue Cards**: Beautiful cards showing venue details
- **Match Scoring**: Color-coded compatibility scores
- **Metadata Display**: Contact info, ratings, capacity, event types
- **Interactive Elements**: Expandable reasoning logs

### 💬 Chat Interface
- **Session Management**: Persistent conversations with unique session IDs
- **Message History**: Complete chat history with timestamps
- **Quick Examples**: Pre-built prompts for testing
- **API Status**: Real-time backend connection monitoring

## File Structure

```
ui/
├── main.py           # Main Streamlit application
├── config.py         # Configuration settings
├── utils.py          # Utility functions for parsing and formatting
├── requirements.txt  # UI-specific dependencies
└── README.md        # This file
```

## Configuration

The UI can be configured through `config.py`:

- **API_BASE_URL**: Backend API endpoint (default: http://localhost:8000)
- **UI settings**: Title, icon, layout preferences
- **Display limits**: Max venues per row, reasoning steps to show
- **Example prompts**: Pre-configured test prompts

## Key Components

### 1. Streaming Handler (`stream_agent_response()`)
Handles real-time streaming from the FastAPI backend:
- Processes Server-Sent Events (SSE)
- Updates UI in real-time
- Manages reasoning and content display

### 2. Venue Parser (`parse_venue_results()`)
Extracts venue information from agent responses:
- Supports both JSON and text formats
- Handles metadata extraction
- Creates structured venue objects

### 3. UI Components
- **Venue Cards**: Rich display of venue information
- **Reasoning Box**: Shows agent's thinking process
- **Chat Messages**: Formatted user/assistant messages
- **Sidebar**: Session management and quick actions

## Usage

### Starting the UI

From the project root:
```bash
# Run UI only
make run-ui

# Run both backend and UI
make run-all
```

Or directly:
```bash
cd ui
streamlit run main.py --server.port 8501
```

### Example Interactions

1. **Wedding Venue Search**:
   ```
   "I need a venue for a wedding in Boston for 150 guests with outdoor space"
   ```

2. **Corporate Event**:
   ```
   "Find me a conference room in New York for 50 people with A/V equipment"
   ```

3. **Birthday Party**:
   ```
   "Looking for a birthday party venue in San Francisco for 30 kids"
   ```

### Viewing Agent Reasoning

- **Real-time**: Watch reasoning appear in orange boxes during streaming
- **Historical**: Click "🧠 View Agent Reasoning" to see past reasoning steps
- **Tool Tracking**: See when tools start/complete execution

### Venue Information

Each venue card displays:
- **Business Name** and **Match Score**
- **Location** (city, state)
- **Venue Type** and **Description**
- **Contact Information** (phone, email, website)
- **Capacity** and **Rating**
- **Event Types** and **Languages**

## Customization

### Adding New Venue Fields

1. Update `parse_venue_metadata()` in `utils.py`
2. Modify `display_venue_card()` in `main.py`
3. Add new styling in the CSS section

### Changing UI Theme

1. Modify `COLORS` in `config.py`
2. Update CSS styles in `main.py`
3. Change icons and layout preferences

### Adding New Features

1. Create new functions in `utils.py`
2. Add UI components in `main.py`
3. Update configuration in `config.py`

## API Integration

The UI communicates with the FastAPI backend through:

### Streaming Endpoint
```
POST /stream
{
  "session": "session_id",
  "user_id": "user_id", 
  "prompt": "user_message",
  "organization_id": "org_id"
}
```

### Response Format
Server-Sent Events with JSON payloads:
```json
{
  "id": "chunk_id",
  "type": "response|response.start|response.end",
  "category": "text.chunk|reasoning|reasoning.chunk|interrupt",
  "content": "chunk_content"
}
```

## Troubleshooting

### Common Issues

1. **API Not Connected**
   - Check if backend is running on port 8000
   - Verify `API_BASE_URL` in config.py
   - Look for network connectivity issues

2. **Streaming Not Working**
   - Ensure proper CORS configuration
   - Check browser developer tools for errors
   - Verify SSE support in browser

3. **Venues Not Displaying**
   - Check venue parsing logic in `parse_venue_results()`
   - Verify agent response format
   - Look at browser console for JavaScript errors

### Debug Mode

Enable debug logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Health Check

The sidebar shows real-time API status. Green means connected, red means issues.

## Development

### Local Development

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Start development server:
   ```bash
   streamlit run main.py --server.runOnSave true
   ```

### Testing

Test individual components:
```bash
# Test venue parsing
python -c "from utils import parse_venue_results; print(parse_venue_results('test'))"

# Test API connection
python -c "import requests; print(requests.get('http://localhost:8000/heartbeat').json())"
```

## Production Deployment

For production deployment:

1. Update `config.py` with production API URL
2. Set proper environment variables
3. Configure security headers
4. Use reverse proxy (nginx) for SSL
5. Monitor with health checks

## Contributing

When contributing to the UI:

1. Follow Streamlit best practices
2. Update utility functions for reusability
3. Add proper error handling
4. Test with different venue data formats
5. Update documentation

## Support

For issues with the UI:
1. Check the troubleshooting section
2. Review logs in browser developer tools
3. Verify backend connectivity
4. Test with example prompts first 