"""AWS authentication utilities."""

import boto3
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.voice_based_aws_agent.config.config import AgentConfig

def get_aws_session(profile_name=None, region=None):
    """
    Create an AWS session using the specified profile and region.
    
    Args:
        profile_name (str, optional): AWS profile name to use. Defaults to None.
        region (str, optional): AWS region to use. Defaults to None.
        
    Returns:
        boto3.Session: Authenticated AWS session
    """
    config = AgentConfig()
    profile = profile_name or config.profile_name
    region = region or config.region
    
    try:
        session = boto3.Session(profile_name=profile, region_name=region)
        # Test the session by making a simple API call
        session.client('sts').get_caller_identity()
        return session
    except Exception as e:
        print(f"Error creating AWS session: {str(e)}")
        print(f"Using profile: {profile}, region: {region}")
        raise
