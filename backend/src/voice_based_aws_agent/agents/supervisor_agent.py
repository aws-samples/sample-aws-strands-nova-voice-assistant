"""
Supervisor Agent - Pure Router
Routes user queries to appropriate specialized agents without any tools or reasoning.
"""

from strands import Agent
from typing import Dict, Any
from ..config.conversation_config import ConversationConfig, log_conversation_config
from ..config.config import create_bedrock_model
import logging

logger = logging.getLogger(__name__)


class SupervisorAgent(Agent):
    """
    Supervisor Agent that acts as a pure router.
    No tools, no reasoning - just routing based on query type.
    """

    def __init__(self, specialized_agents: Dict[str, Agent], config=None):
        """
        Initialize supervisor with references to specialized agents.

        Args:
            specialized_agents: Dictionary mapping agent names to agent instances
            config: AgentConfig instance for AWS profile and region settings
        """
        # Create properly configured Bedrock model with specified profile
        bedrock_model = create_bedrock_model(config)

        # Create conversation manager for supervisor (smaller window since it just routes)
        conversation_manager = ConversationConfig.create_conversation_manager(
            "supervisor"
        )

        # Initialize Strands Agent with system prompt but no tools
        system_prompt = self._get_routing_instructions()
        super().__init__(
            model=bedrock_model,
            system_prompt=system_prompt,
            tools=[],  # No tools for pure router
            conversation_manager=conversation_manager,
        )

        self.specialized_agents = specialized_agents

        # Log configuration
        logger.info(
            "SupervisorAgent initialized with BedrockModel (configured profile, us-east-1, Claude 3 Haiku)"
        )
        log_conversation_config("SupervisorAgent", conversation_manager)
        logger.info(
            f"Supervisor initialized with agents: {list(specialized_agents.keys())} and conversation management"
        )

    def _get_routing_instructions(self) -> str:
        """Get the routing instructions for the supervisor."""
        return """
You are a Supervisor Agent that acts as a pure router for AWS-related queries ONLY. Your job is to:

1. First, validate that the query is AWS-related
2. If non-AWS, politely redirect to AWS topics
3. For AWS queries, determine which specialized agent should handle it
4. Route the query to the appropriate agent
5. Return the agent's response

AWS QUERY VALIDATION:
- ONLY handle queries about AWS services, operations, or infrastructure
- Reject queries about: general programming, non-AWS cloud providers, personal topics, entertainment, etc.
- For non-AWS queries, respond: "I'm specialized in AWS services only. Please ask about EC2, SSM, Backup, or other AWS services."

ROUTING RULES (for valid AWS queries):
- EC2-related queries (instances, status, management) → EC2Agent
- SSM-related queries (commands, documents, patch management) → SSMAgent  
- Backup-related queries (backup jobs, plans, vaults) → BackupAgent
- General AWS queries that don't fit above → EC2Agent (default)

CONVERSATION CONTEXT:
- Remember which agents handled recent queries
- Consider conversation flow when routing follow-up questions
- Route follow-up questions to the same agent when contextually relevant

DO NOT:
- Use any tools yourself
- Perform reasoning about AWS operations
- Make AWS API calls
- Provide technical solutions
- Handle non-AWS queries

ALWAYS:
- Validate query is AWS-related first
- Route to exactly one specialized agent (for AWS queries)
- Pass the original user query unchanged to agents
- Return the specialized agent's response
- Consider conversation history for routing decisions
"""

    async def route_query(self, query: str) -> str:
        """
        Route a query to the appropriate specialized agent.

        Args:
            query: User query to route

        Returns:
            Response from the specialized agent
        """
        logger.info(f"Routing query: {query}")

        # Determine which agent to route to
        agent_name = self._determine_agent(query)

        if agent_name not in self.specialized_agents:
            logger.error(f"Agent {agent_name} not found in specialized agents")
            return f"Error: Unable to route query - {agent_name} not available"

        # Route to specialized agent
        specialized_agent = self.specialized_agents[agent_name]
        logger.info(f"Routing to {agent_name}")

        try:
            # Use the Strands Agent's direct call method
            response = specialized_agent(query)
            logger.info(f"Received response from {agent_name}")
            return response

        except Exception as e:
            logger.error(f"Error from {agent_name}: {str(e)}")
            return f"Error: {agent_name} encountered an issue: {str(e)}"

    def _determine_agent(self, query: str) -> str:
        """
        Determine which agent should handle the query based on keywords.

        Args:
            query: User query

        Returns:
            Name of the agent to route to
        """
        query_lower = query.lower()

        # SSM keywords
        ssm_keywords = [
            "ssm",
            "systems manager",
            "patch",
            "command",
            "document",
            "run command",
            "session manager",
            "parameter store",
            "cloudwatch agent",
            "install",
            "configure",
        ]

        # Backup keywords
        backup_keywords = [
            "backup",
            "restore",
            "vault",
            "backup plan",
            "backup job",
            "recovery",
            "snapshot",
        ]

        # EC2 keywords (and default)
        ec2_keywords = [
            "ec2",
            "instance",
            "server",
            "vm",
            "virtual machine",
            "compute",
            "ami",
            "security group",
            "vpc",
        ]

        # Check for SSM
        if any(keyword in query_lower for keyword in ssm_keywords):
            return "SSMAgent"

        # Check for Backup
        if any(keyword in query_lower for keyword in backup_keywords):
            return "BackupAgent"

        # Default to EC2Agent for general queries
        return "EC2Agent"
