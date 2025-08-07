"""
EC2 Specialized Agent
Handles all EC2-related queries with full reasoning and AWS API access.
"""

from strands import Agent
from strands_tools import use_aws
from ..config.conversation_config import ConversationConfig, log_conversation_config
from ..config.config import create_bedrock_model
from ..utils.prompt_consent import get_consent_instructions
import logging

logger = logging.getLogger(__name__)


class EC2Agent(Agent):
    """
    Specialized agent for EC2 operations.
    Has access to use_aws tool and performs full reasoning.
    """

    def __init__(self, config=None):
        # Create properly configured Bedrock model
        bedrock_model = create_bedrock_model(config)

        # Create conversation manager for EC2 operations
        conversation_manager = ConversationConfig.create_conversation_manager("ec2")

        # Initialize Strands Agent with system prompt, tools, and conversation management
        system_prompt = self._get_instructions()
        super().__init__(
            model=bedrock_model,
            system_prompt=system_prompt,
            tools=[use_aws],
            conversation_manager=conversation_manager,
        )

        # Log configuration
        logger.info(
            "EC2Agent initialized with BedrockModel and consent-aware prompts (configured profile, us-east-1, Claude 3 Haiku)"
        )
        log_conversation_config("EC2Agent", conversation_manager)

    def _get_instructions(self) -> str:
        """Get the instructions for the EC2 agent."""
        base_instructions = """
You are an EC2 Specialized Agent. You are an expert in Amazon EC2 and related AWS services ONLY.

IMPORTANT: You ONLY handle AWS EC2-related queries. If a user asks about non-AWS topics, respond: "I specialize in AWS EC2 services only. Please ask about EC2 instances, AMIs, security groups, or other AWS services."

Your responsibilities:
- Handle all EC2-related queries (instances, AMIs, security groups, etc.)
- Use the use_aws tool to make AWS API calls
- Perform reasoning to understand what the user wants
- Provide detailed, helpful responses
- Handle error cases gracefully
- Maintain conversation context for related queries

Available tool:
- use_aws: Make AWS CLI API calls

Key capabilities:
- List and describe EC2 instances
- Start/stop/reboot instances
- Get instance status and health
- Manage security groups
- Work with AMIs
- Handle VPC-related queries
- Provide cost and performance insights

Conversation context:
- Remember previous queries about specific instances
- Reference earlier operations when relevant
- Maintain state awareness across related requests

Always:
- Understand the user's intent before taking action
- Use appropriate AWS regions (default: us-east-1)
- Provide clear explanations of what you're doing
- Handle errors gracefully and suggest alternatives
- Ask for clarification if the request is ambiguous
- Reference previous conversation context when helpful

Example queries you handle:
- "List all EC2 instances"
- "What's the status of instance i-1234567890abcdef0?"
- "Start the instances in the dev environment"
- "Show me instances that are stopped"
- "What security groups are attached to my instances?"
- "How are those instances I asked about earlier doing?"
"""
        
        # Add consent instructions
        consent_instructions = get_consent_instructions()
        
        return base_instructions + "\n\n" + consent_instructions
