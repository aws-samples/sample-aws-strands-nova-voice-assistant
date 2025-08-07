"""
Integration for the AWS Strands Supervisor Agent.
"""

import json
import logging
import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("SupervisorAgentIntegration")


class SupervisorAgentIntegration:
    """
    Integration class for the AWS Strands supervisor agent.
    """

    def __init__(self, config=None):
        """Initialize the integration with AWS Strands orchestrator."""
        self.config = config
        self.orchestrator = None

        try:
            # Import and initialize the orchestrator
            from src.voice_based_aws_agent.agents.orchestrator import AgentOrchestrator
            from src.voice_based_aws_agent.config.config import AgentConfig
            from src.voice_based_aws_agent.config.tool_config import (
                setup_tool_environment,
            )
            from tools.supervisor_tool import set_orchestrator
            import os

            # Set AWS profile if provided in config
            if config and hasattr(config, "profile_name") and config.profile_name:
                os.environ["AWS_PROFILE"] = config.profile_name
                logger.info(f"Set AWS_PROFILE to: {config.profile_name}")

            # Setup tool environment
            setup_tool_environment()

            # Initialize the orchestrator with config
            self.orchestrator = AgentOrchestrator(config)

            # Set the orchestrator for the supervisor tool
            set_orchestrator(self.orchestrator)

            logger.info("AWS Strands orchestrator initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize AWS Strands orchestrator: {e}")
            logger.info("Falling back to placeholder mode")
            self.orchestrator = None

    async def query(self, query_text):
        """
        Process a query through the AWS Strands supervisor agent.

        Args:
            query_text: The user's query

        Returns:
            str: The response from the agent
        """
        try:
            logger.info(f"Processing query: {query_text[:100]}...")

            # Handle input as either string or JSON
            if isinstance(query_text, str):
                try:
                    # Try to parse as JSON first
                    query_json = json.loads(query_text)
                    if "query" in query_json:
                        actual_query = query_json["query"]
                    else:
                        actual_query = query_text
                except json.JSONDecodeError:
                    # If not JSON, use as plain text
                    actual_query = query_text
            else:
                # If it's already a dict/object, extract the query
                actual_query = query_text.get("query", str(query_text))

            # If orchestrator is available, use it
            if self.orchestrator:
                try:
                    response = await self.orchestrator.process_query(actual_query)
                    logger.info(
                        "Query processed successfully by AWS Strands orchestrator"
                    )

                    # Ensure response is a string and limit length for voice
                    if hasattr(response, "content"):
                        response_text = response.content
                    elif isinstance(response, dict):
                        response_text = response.get("content", str(response))
                    else:
                        response_text = str(response)

                    # Limit response length for voice
                    if len(response_text) > 800:
                        response_text = (
                            response_text[:800] + "... (truncated for voice)"
                        )

                    return response_text

                except Exception as e:
                    logger.error(f"Error processing query with orchestrator: {e}")
                    return f"Sorry, I encountered an error processing your request: {str(e)}"

            # Fallback to placeholder responses
            else:
                logger.warning(
                    "Using placeholder response - orchestrator not available"
                )
                if "ec2" in actual_query.lower() or "instance" in actual_query.lower():
                    response = "I can help you with EC2 instances, but the AWS Strands orchestrator is not fully initialized. Please check the backend logs for configuration issues."
                elif (
                    "ssm" in actual_query.lower()
                    or "systems manager" in actual_query.lower()
                ):
                    response = "I can help you with AWS Systems Manager, but the AWS Strands orchestrator is not fully initialized. Please check the backend logs for configuration issues."
                elif "backup" in actual_query.lower():
                    response = "I can help you with AWS Backup, but the AWS Strands orchestrator is not fully initialized. Please check the backend logs for configuration issues."
                else:
                    response = f"I received your query: '{actual_query}'. However, the AWS Strands orchestrator is not fully initialized. Please check the backend logs for configuration issues."

                return response

        except Exception as e:
            logger.error(f"Error in supervisor agent integration: {e}")
            return f"Sorry, I encountered an error processing your request: {str(e)}"

    def shutdown(self):
        """Shutdown the integration."""
        if self.orchestrator and hasattr(self.orchestrator, "shutdown"):
            self.orchestrator.shutdown()
        logger.info("SupervisorAgentIntegration shutdown")
