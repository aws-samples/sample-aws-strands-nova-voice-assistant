"""
Conversation Management Configuration
Handles conversation context management for multi-agent systems.
"""

import logging
from typing import Optional
from strands.agent.conversation_manager import (
    ConversationManager, 
    SlidingWindowConversationManager,
    NullConversationManager
)

logger = logging.getLogger(__name__)

class ConversationConfig:
    """Configuration for conversation management across agents."""
    
    # Default window sizes for different agent types
    DEFAULT_WINDOW_SIZES = {
        "supervisor": 20,    # Supervisor needs less context (just routing)
        "ec2": 40,          # EC2 operations may need more context
        "ssm": 50,          # SSM operations often involve multi-step processes
        "backup": 30,       # Backup operations moderate context needs
        "default": 40       # Default for any unspecified agent
    }
    
    @classmethod
    def create_conversation_manager(
        cls, 
        agent_type: str = "default",
        window_size: Optional[int] = None,
        enable_management: bool = True
    ) -> ConversationManager:
        """
        Create an appropriate conversation manager for an agent.
        
        Args:
            agent_type: Type of agent (supervisor, ec2, ssm, backup)
            window_size: Custom window size (overrides defaults)
            enable_management: Whether to enable conversation management
            
        Returns:
            ConversationManager instance
        """
        if not enable_management:
            logger.info(f"Creating NullConversationManager for {agent_type}")
            return NullConversationManager()
        
        # Determine window size
        if window_size is None:
            window_size = cls.DEFAULT_WINDOW_SIZES.get(
                agent_type.lower(), 
                cls.DEFAULT_WINDOW_SIZES["default"]
            )
        
        logger.info(f"Creating SlidingWindowConversationManager for {agent_type} with window_size={window_size}")
        return SlidingWindowConversationManager(window_size=window_size)
    
    @classmethod
    def get_recommended_config(cls, agent_type: str) -> dict:
        """
        Get recommended conversation configuration for an agent type.
        
        Args:
            agent_type: Type of agent
            
        Returns:
            Dictionary with recommended configuration
        """
        configs = {
            "supervisor": {
                "window_size": 20,
                "rationale": "Supervisor only routes queries, needs minimal context",
                "enable_management": True
            },
            "ec2": {
                "window_size": 40,
                "rationale": "EC2 operations may reference previous instance states",
                "enable_management": True
            },
            "ssm": {
                "window_size": 50,
                "rationale": "SSM operations often involve multi-step processes and command sequences",
                "enable_management": True
            },
            "backup": {
                "window_size": 30,
                "rationale": "Backup operations may reference previous backup states",
                "enable_management": True
            }
        }
        
        return configs.get(agent_type.lower(), {
            "window_size": 40,
            "rationale": "Default configuration for unspecified agent type",
            "enable_management": True
        })

def log_conversation_config(agent_type: str, conversation_manager: ConversationManager):
    """
    Log conversation configuration for debugging.
    
    Args:
        agent_type: Type of agent
        conversation_manager: The conversation manager instance
    """
    manager_type = type(conversation_manager).__name__
    
    if isinstance(conversation_manager, SlidingWindowConversationManager):
        window_size = getattr(conversation_manager, 'window_size', 'unknown')
        logger.info(f"{agent_type} conversation config: {manager_type} (window_size={window_size})")
    else:
        logger.info(f"{agent_type} conversation config: {manager_type}")
