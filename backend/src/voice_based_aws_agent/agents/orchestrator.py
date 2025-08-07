"""
Agent Orchestrator
Manages the multi-agent system and provides the main interface.
"""

import logging
from typing import Dict, Any
from .supervisor_agent import SupervisorAgent
from .ec2_agent import EC2Agent
from .ssm_agent import SSMAgent
from .backup_agent import BackupAgent
from ..config.tool_config import setup_tool_environment, get_tool_config
from ..config.conversation_config import ConversationConfig

logger = logging.getLogger(__name__)


class AgentOrchestrator:
    """
    Orchestrates the multi-agent system.
    Creates and manages all agents and provides the main query interface.
    """

    def __init__(self, config=None):
        """Initialize the orchestrator with all agents."""
        self.config = config
        self.specialized_agents = {}
        self.supervisor = None
        self._setup_environment()
        self._initialize_agents()
        logger.info("Agent Orchestrator initialized with conversation management")

    def _setup_environment(self):
        """Set up the environment for tool operations."""
        logger.info("Setting up tool environment...")
        setup_tool_environment()

        # Log the current configuration
        config = get_tool_config()
        logger.info(f"Tool configuration: {config}")

    def _initialize_agents(self):
        """Initialize all specialized agents and the supervisor."""
        try:
            # Create specialized agents (each with their own conversation manager)
            logger.info("Creating specialized agents with conversation management...")
            self.specialized_agents = {
                "EC2Agent": EC2Agent(self.config),
                "SSMAgent": SSMAgent(self.config),
                "BackupAgent": BackupAgent(self.config),
            }

            # Create supervisor with references to specialized agents
            logger.info("Creating supervisor agent with conversation management...")
            self.supervisor = SupervisorAgent(self.specialized_agents, self.config)

            logger.info(
                f"Initialized {len(self.specialized_agents)} specialized agents with conversation management"
            )

        except Exception as e:
            logger.error(f"Failed to initialize agents: {str(e)}")
            raise

    async def process_query(self, query: str) -> str:
        """
        Process a user query through the multi-agent system.

        Args:
            query: User query to process

        Returns:
            Response from the appropriate specialized agent
        """
        if not self.supervisor:
            return "Error: Agent system not properly initialized"

        try:
            logger.info(f"Processing query: {query}")
            response = await self.supervisor.route_query(query)
            logger.info("Query processed successfully")
            return response

        except Exception as e:
            logger.error(f"Error processing query: {str(e)}")
            return f"Error: Unable to process query - {str(e)}"

    def get_agent_status(self) -> Dict[str, Any]:
        """
        Get status of all agents in the system.

        Returns:
            Dictionary with agent status information
        """
        # Get conversation management configurations
        conversation_configs = {}
        for agent_type in ["supervisor", "ec2", "ssm", "backup"]:
            conversation_configs[agent_type] = (
                ConversationConfig.get_recommended_config(agent_type)
            )

        return {
            "supervisor": "active" if self.supervisor else "inactive",
            "specialized_agents": {
                name: "active" for name in self.specialized_agents.keys()
            },
            "total_agents": len(self.specialized_agents)
            + (1 if self.supervisor else 0),
            "tool_config": get_tool_config(),
            "conversation_management": {
                "enabled": True,
                "configurations": conversation_configs,
                "manager_type": "SlidingWindowConversationManager",
            },
        }

    def shutdown(self):
        """Shutdown all agents gracefully."""
        logger.info("Shutting down agent orchestrator")
        # Add any cleanup logic here if needed
        self.specialized_agents.clear()
        self.supervisor = None
