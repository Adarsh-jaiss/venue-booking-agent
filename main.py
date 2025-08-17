import asyncio
import logging
import sys
import uuid
from datetime import datetime
from typing import Optional

import contextvars
from agent.main import initialize, stream, invoke, resume, agent_ctx


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('agent_session.log', mode='a')
    ]
)

logger = logging.getLogger(__name__)


class TerminalAgent:
    def __init__(self):
        self.session_id = str(uuid.uuid4())
        self.user_id = "terminal_user"
        self.organization_id = "default_org"
        self.agent = None
        
    async def initialize_agent(self):
        """Initialize the agent and set it in context"""
        try:
            logger.info("Initializing agent...")
            self.agent = await initialize()
            agent_ctx.set(self.agent)
            logger.info(f"Agent initialized successfully with session ID: {self.session_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize agent: {e}")
            return False
    
    async def handle_stream_response(self, prompt: str):
        """Handle streaming response from agent"""
        logger.info(f"Processing streaming request: {prompt[:50]}...")
        
        try:
            print("\n🤖 Agent (streaming):")
            async for chunk in stream(prompt, self.session_id, self.user_id, self.organization_id):
                # Parse the Server-Sent Events format
                if chunk.startswith("data: "):
                    data = chunk[6:].strip()  # Remove "data: " prefix
                    if data and data != "[DONE]":
                        print(data, end="", flush=True)
            print("\n")  # Add newline after streaming is complete
            
        except Exception as e:
            logger.error(f"Error during streaming: {e}")
            print(f"\n❌ Error during streaming: {e}")
    
    async def handle_invoke_response(self, prompt: str):
        """Handle regular invoke response from agent"""
        logger.info(f"Processing invoke request: {prompt[:50]}...")
        
        try:
            result = await invoke(prompt, self.session_id, self.user_id, self.organization_id)
            print(f"\n🤖 Agent: {result['message']}")
            
        except Exception as e:
            logger.error(f"Error during invoke: {e}")
            print(f"\n❌ Error during invoke: {e}")
    
    async def handle_resume(self, answers: dict):
        """Handle resume functionality"""
        logger.info(f"Resuming agent with answers: {answers}")
        
        try:
            print("\n🤖 Agent (resuming):")
            async for chunk in resume(answers, self.session_id, self.user_id, self.organization_id):
                # Parse the Server-Sent Events format
                if chunk.startswith("data: "):
                    data = chunk[6:].strip()  # Remove "data: " prefix
                    if data and data != "[DONE]":
                        print(data, end="", flush=True)
            print("\n")  # Add newline after streaming is complete
            
        except Exception as e:
            logger.error(f"Error during resume: {e}")
            print(f"\n❌ Error during resume: {e}")
    
    def print_help(self):
        """Print available commands"""
        help_text = """
📋 Available Commands:
  /help           - Show this help message
  /stream <msg>   - Send message with streaming response
  /invoke <msg>   - Send message with regular response
  /resume         - Resume conversation (interactive mode)
  /session        - Show current session info
  /new            - Start new session
  /quit or /exit  - Exit the application
  
💡 Tips:
  - Just type your message for streaming mode (default)
  - Use /stream for explicit streaming
  - Use /invoke for non-streaming responses
  - Session persists across messages within same run
        """
        print(help_text)
    
    def print_session_info(self):
        """Print current session information"""
        print(f"""
📊 Session Information:
  Session ID: {self.session_id}
  User ID: {self.user_id}
  Organization ID: {self.organization_id}
  Agent Status: {'✅ Initialized' if self.agent else '❌ Not initialized'}
        """)
    
    def start_new_session(self):
        """Start a new session"""
        old_session = self.session_id
        self.session_id = str(uuid.uuid4())
        logger.info(f"Started new session. Old: {old_session}, New: {self.session_id}")
        print(f"🔄 Started new session: {self.session_id}")
    
    async def interactive_resume(self):
        """Interactive mode for resume functionality"""
        print("\n📝 Resume Mode - Enter key-value pairs (type 'done' when finished):")
        answers = {}
        
        while True:
            try:
                key = input("Key (or 'done' to finish): ").strip()
                if key.lower() == 'done':
                    break
                if not key:
                    continue
                    
                value = input(f"Value for '{key}': ").strip()
                answers[key] = value
                print(f"✅ Added: {key} = {value}")
                
            except KeyboardInterrupt:
                print("\n❌ Resume cancelled")
                return
        
        if answers:
            await self.handle_resume(answers)
        else:
            print("No answers provided for resume.")
    
    async def run(self):
        """Main terminal interface loop"""
        # Initialize agent
        if not await self.initialize_agent():
            print("❌ Failed to initialize agent. Exiting...")
            return
        
        print("🚀 Agent Terminal Interface Started!")
        print("Type '/help' for available commands or just start typing to chat.")
        self.print_session_info()
        
        while True:
            try:
                user_input = input("\n👤 You: ").strip()
                
                if not user_input:
                    continue
                
                # Handle special commands
                if user_input.startswith('/'):
                    command_parts = user_input.split(' ', 1)
                    command = command_parts[0].lower()
                    
                    if command in ['/quit', '/exit']:
                        print("👋 Goodbye!")
                        logger.info("User requested exit")
                        break
                    
                    elif command == '/help':
                        self.print_help()
                    
                    elif command == '/session':
                        self.print_session_info()
                    
                    elif command == '/new':
                        self.start_new_session()
                    
                    elif command == '/resume':
                        await self.interactive_resume()
                    
                    elif command == '/stream':
                        if len(command_parts) > 1:
                            await self.handle_stream_response(command_parts[1])
                        else:
                            print("❌ Please provide a message after /stream")
                    
                    elif command == '/invoke':
                        if len(command_parts) > 1:
                            await self.handle_invoke_response(command_parts[1])
                        else:
                            print("❌ Please provide a message after /invoke")
                    
                    else:
                        print(f"❌ Unknown command: {command}. Type '/help' for available commands.")
                
                else:
                    # Default to streaming mode for regular messages
                    await self.handle_stream_response(user_input)
            
            except KeyboardInterrupt:
                print("\n\n👋 Interrupted by user. Goodbye!")
                logger.info("Application interrupted by user")
                break
            
            except Exception as e:
                logger.error(f"Unexpected error in main loop: {e}")
                print(f"❌ Unexpected error: {e}")
                print("🔄 Continuing... Type '/quit' to exit.")


async def main():
    """Entry point for the application"""
    start_time = datetime.now()
    logger.info(f"Application started at {start_time}")
    
    try:
        terminal_agent = TerminalAgent()
        await terminal_agent.run()
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        print(f"💥 Fatal error: {e}")
    finally:
        end_time = datetime.now()
        logger.info(f"Application ended at {end_time}. Total runtime: {end_time - start_time}")


if __name__ == "__main__":
    # Ensure we're running in an async context
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Application terminated by user.")
    except Exception as e:
        print(f"💥 Failed to start application: {e}")
        logging.error(f"Failed to start application: {e}")