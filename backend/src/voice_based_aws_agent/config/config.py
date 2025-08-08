"""Configuration settings for the voice-based AWS agent."""

import os
import boto3
from dataclasses import dataclass
from strands.models import BedrockModel


@dataclass
class AgentConfig:
    """Configuration for the agent."""

    model_id: str = "anthropic.claude-3-haiku-20240307-v1:0"
    region: str = "us-east-1"
    profile_name: str = None
    temperature: float = 0.0
    max_tokens: int = 2048  # Recommended max tokens for better responses
    request_timeout: int = 300  # Timeout in seconds for API requests

    def __post_init__(self):
        """Set default profile_name if not provided."""
        if self.profile_name is None:
            self.profile_name = os.environ.get("AWS_PROFILE", "default")


@dataclass
class VoiceConfig:
    """Configuration for voice input/output."""

    sample_rate: int = 16000
    chunk_size: int = 1024
    channels: int = 1
    format_type: int = 8  # pyaudio.paInt16
    timeout_seconds: int = 5  # Silence timeout


def create_bedrock_model(config: AgentConfig = None) -> BedrockModel:
    """
    Create a properly configured BedrockModel for Strands agents.

    Args:
        config: AgentConfig instance, creates default if None

    Returns:
        BedrockModel configured with the specified profile and region
    """
    if config is None:
        config = AgentConfig()

    # Create a custom boto3 session with the specified profile
    session = boto3.Session(region_name=config.region, profile_name=config.profile_name)

    # Create a Bedrock model with the custom session
    bedrock_model = BedrockModel(model_id=config.model_id, boto_session=session)

    return bedrock_model
