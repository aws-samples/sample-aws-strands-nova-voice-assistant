"""
Tool Configuration Module
Handles tool-specific configurations including consent bypass for automated agents.
"""

import os
import logging

logger = logging.getLogger(__name__)

def setup_tool_environment():
    """
    Set up environment variables for tool configuration.
    This includes bypassing tool consent prompts for automated agent operations.
    """
    # Set BYPASS_TOOL_CONSENT to skip user confirmation prompts
    # This is essential for voice agents and automated systems where
    # interactive prompts would break the event loop
    os.environ["BYPASS_TOOL_CONSENT"] = "true"
    
    # Additional tool configurations can be added here
    logger.info("Tool environment configured - consent prompts bypassed for automated operation")

def is_tool_consent_bypassed() -> bool:
    """
    Check if tool consent is bypassed.
    
    Returns:
        bool: True if consent is bypassed, False otherwise
    """
    return os.getenv("BYPASS_TOOL_CONSENT", "false").lower() in ["true", "1", "yes"]

def get_tool_config() -> dict:
    """
    Get current tool configuration.
    
    Returns:
        dict: Current tool configuration settings
    """
    return {
        "bypass_consent": is_tool_consent_bypassed(),
        "environment_vars": {
            "BYPASS_TOOL_CONSENT": os.getenv("BYPASS_TOOL_CONSENT", "false")
        }
    }
