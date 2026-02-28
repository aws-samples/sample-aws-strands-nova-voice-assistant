"""
Supervisor Tool for Voice Agent Integration
Provides the interface between Nova Sonic and the multi-agent system.
"""

import asyncio
import logging
from strands import tool

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger("supervisor_tool")

# Global orchestrator instance
_orchestrator = None

def set_orchestrator(orchestrator):
    """Set the global orchestrator instance."""
    global _orchestrator
    _orchestrator = orchestrator
    logger.info("Orchestrator set for supervisor tool")

def get_orchestrator():
    """Get the global orchestrator instance."""
    global _orchestrator
    if _orchestrator is None:
        logger.info("Creating new orchestrator instance")
        from src.voice_based_aws_agent.agents.orchestrator import AgentOrchestrator
        _orchestrator = AgentOrchestrator()
    return _orchestrator

async def process_query_async(query: str) -> str:
    """
    Process a query through the multi-agent system asynchronously.
    
    Args:
        query: User query to process
        
    Returns:
        Response from the appropriate specialized agent
    """
    try:
        orchestrator = get_orchestrator()
        response = await orchestrator.process_query(query)
        return response
        
    except Exception as e:
        logger.error(f"Supervisor tool error: {str(e)}")
        return f"I encountered an error processing your request: {str(e)}"

@tool(name="supervisorAgent")
def process_aws_query(
    query: str,
) -> str:
    """
    Process AWS operations through specialized agents for EC2, Backup, and SSM.
    
    Args:
        query: The user query about AWS services or operations
    
    Returns:
        str: Response from the appropriate specialized agent
    """
    try:
        logger.info(f"Processing query: {query}")
        
        # Handle async execution in sync context
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If we're already in an event loop, create a new thread
                import concurrent.futures
                import threading
                
                def run_in_thread():
                    new_loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(new_loop)
                    try:
                        return new_loop.run_until_complete(process_query_async(query))
                    finally:
                        new_loop.close()
                
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(run_in_thread)
                    return future.result(timeout=30)  # 30 second timeout
            else:
                # No event loop running, we can use asyncio.run
                return asyncio.run(process_query_async(query))
                
        except RuntimeError as e:
            if "no running event loop" in str(e):
                return asyncio.run(process_query_async(query))
            else:
                raise
            
    except Exception as e:
        error_msg = f"Error in supervisorAgent tool: {str(e)}"
        logger.error(error_msg)
        return error_msg
