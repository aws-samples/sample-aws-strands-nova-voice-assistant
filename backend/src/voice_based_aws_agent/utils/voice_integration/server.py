#!/usr/bin/env python3
"""WebSocket server for BidiAgent voice-based AWS assistant.

Handles WebSocket connections from the frontend, bridging them to a BidiAgent
that processes speech-to-text, tool execution via use_aws, and text-to-speech
in a single bidirectional stream.
"""

import asyncio
import json
import logging
import os
import uuid
import warnings

import websockets
from strands.experimental.bidi import BidiAgent
from strands.session import FileSessionManager
from strands_tools import use_aws

from .bidi_channels import WebSocketBidiInput, WebSocketBidiOutput
from ...config.config import AgentConfig, create_bidi_model
from ...utils.prompt_consent import get_consent_instructions

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("BidiAgentServer")

# Suppress warnings
warnings.filterwarnings("ignore")

# Session / conversation history settings
SESSIONS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "sessions")
MAX_HISTORY_MESSAGES = 20  # Keep last 20 messages (10 turns) to avoid token bloat


def build_system_prompt() -> str:
    """Build the consolidated system prompt for the BidiAgent.

    Merges instructions from the former EC2Agent, SSMAgent, and BackupAgent
    prompts, the dangerous-operation consent protocol, voice output guidelines,
    and non-AWS query rejection instructions into a single prompt.
    """
    consent_protocol = get_consent_instructions()

    return f"""You are a specialized AWS voice assistant. You help users manage their AWS infrastructure using the use_aws tool. You handle EC2, Systems Manager (SSM), and AWS Backup operations directly.

AWS EC2 CAPABILITIES:
- List and describe EC2 instances, AMIs, security groups, and VPCs
- Start, stop, and reboot instances
- Get instance status and health checks
- Manage security groups and key pairs
- Provide cost and performance insights

AWS SYSTEMS MANAGER (SSM) CAPABILITIES:
- Run commands on EC2 instances via SSM
- Manage SSM documents and parameters
- Handle patch management and compliance
- Install and configure software (e.g. CloudWatch agent)
- Session Manager operations
- Inventory management

AWS BACKUP CAPABILITIES:
- List and manage backup jobs, plans, and vaults
- Monitor backup status and health
- Handle restore operations
- Manage backup policies and schedules
- Cost optimization for backups
- Compliance and reporting

TOOL USAGE:
- Use the use_aws tool to make AWS CLI API calls for all services above
- Use appropriate AWS regions (default: us-east-1)
- Handle errors gracefully and suggest alternatives
- Ask for clarification if the request is ambiguous

{consent_protocol}

VOICE OUTPUT GUIDELINES:
- Keep responses concise and conversational — they will be spoken aloud
- Do NOT use markdown formatting (no bullet points, headers, bold, code blocks, or tables)
- Avoid long lists; summarize when possible and offer to provide details if needed
- Use natural, spoken language suitable for text-to-speech output
- Spell out abbreviations on first use when they may be unclear in speech

NON-AWS QUERY HANDLING:
- You ONLY handle AWS-related queries (EC2, SSM, Backup, and related services)
- If a user asks about non-AWS topics, respond: "I'm an AWS voice assistant and can only help with AWS services like EC2, Systems Manager, and Backup. Please ask me about your AWS infrastructure."
- Politely redirect non-AWS conversations back to AWS topics"""



async def websocket_handler(websocket, path, profile_name, region):
    """Handle a single WebSocket connection with a BidiAgent session.

    1. Waits for an optional ``config`` message to extract voice_id and session_id.
    2. Creates the BidiAgent with use_aws, consolidated system prompt, and session manager.
    3. Runs the agent with WebSocket-bridged I/O channels.
    4. Ensures cleanup on completion or error.
    """
    logger.info("New WebSocket connection from %s", websocket.remote_address)

    voice_id = "matthew"
    session_id = None

    # Wait for optional config message from frontend
    try:
        first_msg = await asyncio.wait_for(websocket.recv(), timeout=5.0)
        data = json.loads(first_msg)
        if data.get("type") == "config":
            voice_id = data.get("voice_id", "matthew")
            session_id = data.get("session_id")
            logger.info("Received config: voice_id=%s, session_id=%s", voice_id, session_id)
    except (asyncio.TimeoutError, json.JSONDecodeError):
        logger.info("No config message received, using default voice_id=%s", voice_id)

    # Generate a session ID if the frontend didn't provide one
    if not session_id:
        session_id = str(uuid.uuid4())

    # Ensure use_aws tool operates without interactive prompts
    os.environ["BYPASS_TOOL_CONSENT"] = "true"

    config = AgentConfig(
        profile_name=profile_name,
        region=region or "us-east-1",
        voice_id=voice_id,
    )
    model = create_bidi_model(config)
    system_prompt = build_system_prompt()

    # Set up file-based session manager for conversation persistence
    session_manager = FileSessionManager(
        session_id=session_id,
        storage_dir=os.path.abspath(SESSIONS_DIR),
    )

    agent = BidiAgent(
        model=model,
        tools=[use_aws],
        system_prompt=system_prompt,
        session_manager=session_manager,
    )

    # Trim history if it grew too large from a previous session
    if len(agent.messages) > MAX_HISTORY_MESSAGES:
        agent.messages = agent.messages[-MAX_HISTORY_MESSAGES:]
        logger.info("Trimmed conversation history to last %d messages", MAX_HISTORY_MESSAGES)

    bidi_input = WebSocketBidiInput(websocket)
    bidi_output = WebSocketBidiOutput(websocket)

    # Auto-reconnect loop: Nova Sonic has a 10-minute (600s) max audio stream length.
    # When that limit is hit, we tear down the agent and create a fresh one that
    # inherits the conversation history via the session manager.
    MAX_RETRIES = 50  # ~8 hours of continuous conversation
    for attempt in range(MAX_RETRIES):
        try:
            await agent.run(inputs=[bidi_input], outputs=[bidi_output])
            break  # clean exit (user closed session)
        except Exception as e:
            is_stream_limit = "audio stream length exceeded" in str(e)
            if is_stream_limit and attempt < MAX_RETRIES - 1:
                logger.info("Audio stream limit reached, reconnecting (attempt %d)...", attempt + 1)
                try:
                    restart_msg = {"type": "bidi_connection_restart"}
                    await websocket.send(json.dumps(restart_msg))
                except Exception:
                    pass

                # Create a fresh model + agent, keeping the same session manager
                # so conversation history carries over automatically
                model = create_bidi_model(config)
                agent = BidiAgent(
                    model=model,
                    tools=[use_aws],
                    system_prompt=system_prompt,
                    session_manager=session_manager,
                )
                if len(agent.messages) > MAX_HISTORY_MESSAGES:
                    agent.messages = agent.messages[-MAX_HISTORY_MESSAGES:]
                continue
            else:
                logger.error("BidiAgent error: %s", e, exc_info=True)
                try:
                    error_msg = {"type": "bidi_error", "message": str(e)}
                    await websocket.send(json.dumps(error_msg))
                except Exception:
                    logger.warning("Failed to send error event to frontend")
                break

    logger.info("Cleaning up BidiAgent session")
    await bidi_input.stop()
    await bidi_output.stop()
    logger.info("BidiAgent session cleanup complete")


async def run_server(profile_name=None, region=None, host="localhost", port=80):
    """Start the WebSocket server for BidiAgent voice sessions."""
    async with websockets.serve(
        lambda ws, path: websocket_handler(ws, path, profile_name, region),
        host,
        port,
    ):
        logger.info("BidiAgent WebSocket server started at %s:%s", host, port)
        await asyncio.Future()  # run forever
