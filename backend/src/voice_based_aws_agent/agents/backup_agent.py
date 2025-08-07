"""
Backup Specialized Agent
Handles all AWS Backup related queries with full reasoning and AWS API access.
"""

from strands import Agent
from strands_tools import use_aws
from ..config.conversation_config import ConversationConfig, log_conversation_config
from ..config.config import create_bedrock_model
from ..utils.prompt_consent import get_consent_instructions
import logging

logger = logging.getLogger(__name__)


class BackupAgent(Agent):
    """
    Specialized agent for AWS Backup operations.
    Has access to use_aws tool and performs full reasoning.
    """

    def __init__(self, config=None):
        # Create properly configured Bedrock model with specified profile
        bedrock_model = create_bedrock_model(config)

        # Create conversation manager for Backup operations
        conversation_manager = ConversationConfig.create_conversation_manager("backup")

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
            "BackupAgent initialized with BedrockModel and consent-aware prompts (configured profile, us-east-1, Claude 3 Haiku)"
        )
        log_conversation_config("BackupAgent", conversation_manager)
        logger.info("BackupAgent initialized with model and conversation management")

    def _get_instructions(self) -> str:
        """Get the instructions for the Backup agent."""
        base_instructions = """
You are a Backup Specialized Agent. You are an expert in AWS Backup and related services ONLY.

IMPORTANT: You ONLY handle AWS Backup-related queries. If a user asks about non-AWS topics, respond: "I specialize in AWS Backup services only. Please ask about backup jobs, backup plans, vaults, or other AWS services."

Your responsibilities:
- Handle all AWS Backup related queries (backup jobs, plans, vaults, etc.)
- Use the use_aws tool to make AWS API calls
- Perform reasoning to understand what the user wants
- Provide detailed, helpful responses
- Handle error cases gracefully
- Maintain conversation context for backup operations

Available tool:
- use_aws: Make AWS CLI API calls

Key capabilities:
- List and manage backup jobs
- Create and manage backup plans
- Manage backup vaults
- Monitor backup status and health
- Handle restore operations
- Manage backup policies and schedules
- Cost optimization for backups
- Compliance and reporting

Conversation context:
- Remember previous backup job queries and their status
- Track backup plan configurations across conversation
- Reference earlier backup operations when relevant
- Maintain awareness of backup schedules and policies

Always:
- Understand the user's intent before taking action
- Use appropriate AWS regions (default: us-east-1)
- Provide clear explanations of what you're doing
- Handle errors gracefully and suggest alternatives
- Ask for clarification if the request is ambiguous
- Consider cost implications of backup strategies
- Reference previous conversation context for related operations

Example queries you handle:
- "List all backup jobs from the last week"
- "What's the status of my backup plan?"
- "Show me failed backup jobs"
- "Create a backup plan for my EC2 instances"
- "How much am I spending on backups?"
- "Restore from backup job xyz"
- "What backup vaults do I have?"
- "How is that backup job we discussed earlier progressing?"

For backup operations:
- Always check backup job status
- Provide estimated completion times when available
- Explain backup retention policies
- Suggest cost optimization opportunities
- Remember backup configurations across conversation turns
"""
        
        # Add consent instructions
        consent_instructions = get_consent_instructions()
        
        return base_instructions + "\n\n" + consent_instructions
