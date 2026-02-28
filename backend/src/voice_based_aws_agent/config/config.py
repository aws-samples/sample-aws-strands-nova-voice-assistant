"""Configuration settings for the voice-based AWS agent."""

import boto3
from dataclasses import dataclass
from strands.experimental.bidi.models import BidiNovaSonicModel


@dataclass
class AgentConfig:
    """Configuration for the BidiAgent."""

    region: str = "us-east-1"
    profile_name: str = None
    voice_id: str = "matthew"
    input_sample_rate: int = 16000
    output_sample_rate: int = 24000
    audio_channels: int = 1
    audio_format: str = "pcm"


def create_bidi_model(config: AgentConfig) -> BidiNovaSonicModel:
    """Create a BidiNovaSonicModel configured with the given AgentConfig."""
    session = boto3.Session(
        profile_name=config.profile_name,
        region_name=config.region,
    )
    return BidiNovaSonicModel(
        model_id="amazon.nova-2-sonic-v1:0",
        provider_config={
            "audio": {
                "input_rate": config.input_sample_rate,
                "output_rate": config.output_sample_rate,
                "voice": config.voice_id,
                "channels": config.audio_channels,
                "format": config.audio_format,
            }
        },
        client_config={
            "boto_session": session,
        },
    )
