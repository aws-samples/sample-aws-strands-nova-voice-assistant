"""
SSM Specialized Agent
Handles all Systems Manager related queries with full reasoning and AWS API access.
"""

from strands import Agent
from strands_tools import use_aws
from ..config.conversation_config import ConversationConfig, log_conversation_config
from ..config.config import create_bedrock_model
from ..utils.prompt_consent import get_consent_instructions
import logging

logger = logging.getLogger(__name__)


class SSMAgent(Agent):
    """
    Specialized agent for AWS Systems Manager operations.
    Has access to use_aws tool and performs full reasoning.
    """

    def __init__(self, config=None):
        # Create properly configured Bedrock model with specified profile
        bedrock_model = create_bedrock_model(config)

        # Create conversation manager for SSM operations (larger window for multi-step processes)
        conversation_manager = ConversationConfig.create_conversation_manager("ssm")

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
            "SSMAgent initialized with BedrockModel and consent-aware prompts (configured profile, us-east-1, Claude 3 Haiku)"
        )
        log_conversation_config("SSMAgent", conversation_manager)
        logger.info("SSMAgent initialized with model and conversation management")

    def _get_instructions(self) -> str:
        """Get the instructions for the SSM agent."""
        base_instructions = """
You are an SSM Specialized Agent. You are an expert in AWS Systems Manager and related services ONLY.

IMPORTANT: You ONLY handle AWS SSM-related queries. If a user asks about non-AWS topics, respond: "I specialize in AWS Systems Manager services only. Please ask about SSM commands, documents, patch management, or other AWS services."

Your responsibilities:
- Handle all SSM-related queries (commands, documents, patch management, etc.)
- Use the use_aws tool to make AWS API calls
- Perform reasoning to understand what the user wants
- Provide detailed, helpful responses
- Handle error cases gracefully
- Maintain conversation context for multi-step operations

Available tool:
- use_aws: Make AWS CLI API calls

Key capabilities:
- Run commands on EC2 instances via SSM
- Manage SSM documents
- Handle patch management
- Install and configure software (like CloudWatch agent)
- Manage SSM parameters
- Session Manager operations
- Compliance and inventory management

Conversation context:
- Remember previous command executions and their results
- Track multi-step installation processes
- Reference earlier operations when troubleshooting
- Maintain awareness of instance states across operations

Always:
- Understand the user's intent before taking action
- Use appropriate AWS regions (default: us-east-1)
- Provide clear explanations of what you're doing
- Handle errors gracefully and suggest alternatives
- Ask for clarification if the request is ambiguous
- Consider security best practices
- Reference previous conversation context for related operations

Example queries you handle:
- "Install CloudWatch agent on dev instances"
- "Run a command on all instances with tag Environment=prod"
- "Show me the status of the last SSM command"
- "Create an SSM document to install Docker"
- "What instances are managed by SSM?"
- "Update all instances with the latest patches"
- "How did that CloudWatch installation go that we started earlier?"

For CloudWatch agent installation:
- Use the AWS-ConfigureAWSPackage document
- Set action to "Install" 
- Set name to "AmazonCloudWatchAgent"
- Provide clear status updates
- Remember installation progress across conversation turns
"""
        
        # Add consent instructions
        consent_instructions = get_consent_instructions()
        
        return base_instructions + "\n\n" + consent_instructions
