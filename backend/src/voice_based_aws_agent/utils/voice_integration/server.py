#!/usr/bin/env python3
"""
Simple WebSocket server based on nova-s2s-workshop
"""

import asyncio
import websockets
import json
import logging
import warnings
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from .s2s_session_manager import S2sSessionManager
from src.voice_based_aws_agent.utils.aws_auth import get_aws_session
from src.voice_based_aws_agent.config.config import AgentConfig

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("SimpleNovaServer")

# Suppress warnings
warnings.filterwarnings("ignore")

async def websocket_handler(websocket, path, config):
    """Handle WebSocket connections - simplified version"""
    stream_manager = None
    forward_task = None
    
    logger.info(f"New WebSocket connection from {websocket.remote_address}")
    
    try:
        async for message in websocket:
            try:
                data = json.loads(message)
                if 'body' in data:
                    data = json.loads(data["body"])
                
                if 'event' in data:
                    event_type = list(data['event'].keys())[0]
                    
                    # Initialize stream manager only once per WebSocket connection
                    if stream_manager is None:
                        logger.info("Initializing simple stream manager")
                        stream_manager = S2sSessionManager(
                            model_id='amazon.nova-sonic-v1:0',
                            region='us-east-1',
                            config=config
                        )
                        
                        # Initialize the Bedrock stream
                        await stream_manager.initialize_stream()
                        
                        # Start a task to forward responses from Bedrock to the WebSocket
                        forward_task = asyncio.create_task(forward_responses(websocket, stream_manager))
                    
                    # Store prompt name and content names if provided
                    if event_type == 'promptStart':
                        stream_manager.prompt_name = data['event']['promptStart']['promptName']
                    elif event_type == 'contentStart' and data['event']['contentStart'].get('type') == 'AUDIO':
                        stream_manager.audio_content_name = data['event']['contentStart']['contentName']
                    
                    # Handle audio input separately
                    if event_type == 'audioInput':
                        # Extract audio data
                        prompt_name = data['event']['audioInput']['promptName']
                        content_name = data['event']['audioInput']['contentName']
                        audio_base64 = data['event']['audioInput']['content']
                        
                        # Add to the audio queue
                        stream_manager.add_audio_chunk(prompt_name, content_name, audio_base64)
                    else:
                        # Send other events directly to Bedrock
                        await stream_manager.send_raw_event(data)
                        
            except json.JSONDecodeError:
                logger.error("Invalid JSON received from WebSocket")
            except Exception as e:
                logger.error(f"Error processing WebSocket message: {e}")
                    
    except websockets.exceptions.ConnectionClosed:
        logger.info("WebSocket connection closed")
    except Exception as e:
        logger.error(f"WebSocket handler error: {e}")
    finally:
        # Clean up
        logger.info("Cleaning up WebSocket connection")
        if stream_manager:
            stream_manager.close()
        if forward_task and not forward_task.done():
            forward_task.cancel()
        logger.info("WebSocket connection cleanup complete")

async def forward_responses(websocket, stream_manager):
    """Forward responses from Bedrock to the WebSocket - simplified version"""
    try:
        while stream_manager.is_active:
            # Get next response from the output queue
            response = await stream_manager.output_queue.get()
            
            # Send to WebSocket
            try:
                event = json.dumps(response)
                await websocket.send(event)
            except websockets.exceptions.ConnectionClosed:
                logger.info("WebSocket connection closed during response forwarding")
                break
            except Exception as send_error:
                logger.error(f"Error sending response to WebSocket: {send_error}")
                break
                
    except asyncio.CancelledError:
        logger.info("Response forwarding task cancelled")
    except Exception as e:
        logger.error(f"Error forwarding responses: {e}")
    finally:
        logger.info("Response forwarding stopped")

async def main(host, port, config):
    """Main function to run the WebSocket server"""
    try:
        # Start WebSocket server
        async with websockets.serve(
            lambda ws, path: websocket_handler(ws, path, config),
            host,
            port
        ):
            logger.info(f"Simple WebSocket server started at {host}:{port}")
            
            # Keep the server running forever
            await asyncio.Future()
    except Exception as e:
        logger.error(f"Failed to start WebSocket server: {e}")

async def run_server(profile_name=None, region=None, host="localhost", port=80):
    """Run the simple WebSocket server"""
    # Create agent configuration
    config = AgentConfig(
        profile_name=profile_name,
        region=region or "us-east-1"
    )
    
    # Ensure AWS credentials are available
    session = get_aws_session(config.profile_name)
    if not session:
        logger.error("Failed to get AWS session. Check your credentials.")
        return
    
    try:
        await main(host, port, config)
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Simple Nova S2S WebSocket Server")
    parser.add_argument("--profile", help="AWS profile name")
    parser.add_argument("--region", default="us-east-1", help="AWS region")
    parser.add_argument("--host", default="localhost", help="Host to bind to")
    parser.add_argument("--port", type=int, default=80, help="Port to bind to")
    
    args = parser.parse_args()
    
    asyncio.run(run_server(
        profile_name=args.profile,
        region=args.region,
        host=args.host,
        port=args.port
    ))
