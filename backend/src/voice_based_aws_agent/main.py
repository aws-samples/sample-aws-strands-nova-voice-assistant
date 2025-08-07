#!/usr/bin/env python3
"""
Main entry point for the AWS Strands Nova Voice Assistant.
Simplified version based on nova-s2s-workshop.
"""

import asyncio
import argparse
import os
import sys
import logging
from pathlib import Path

# Add the current directory to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from utils.voice_integration.server import run_server

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("VoiceAssistantMain")


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="AWS Strands Nova Voice Assistant")
    parser.add_argument(
        "--profile",
        default=os.getenv("AWS_PROFILE", "default"),
        help="AWS profile name (default: uses AWS_PROFILE env var or 'default')",
    )
    parser.add_argument(
        "--region",
        default=os.getenv("AWS_DEFAULT_REGION", "us-east-1"),
        help="AWS region (default: us-east-1)",
    )
    parser.add_argument(
        "--voice",
        choices=["matthew", "tiffany", "amy"],
        default="matthew",
        help="Voice ID for responses (default: matthew)",
    )
    parser.add_argument(
        "--host", default="localhost", help="WebSocket server host (default: localhost)"
    )
    parser.add_argument(
        "--port", type=int, default=8080, help="WebSocket server port (default: 8080)"
    )
    parser.add_argument(
        "--text-mode",
        action="store_true",
        help="Use text input/output instead of voice (for testing)",
    )

    args = parser.parse_args()

    # Set environment variable for tool consent bypass
    os.environ["BYPASS_TOOL_CONSENT"] = "true"

    logger.info("=" * 60)
    logger.info("AWS Strands Nova Voice Assistant")
    logger.info("=" * 60)
    logger.info(f"AWS Profile: {args.profile}")
    logger.info(f"AWS Region: {args.region}")
    logger.info(f"Voice: {args.voice}")
    logger.info(f"Server: {args.host}:{args.port}")
    logger.info(f"Text Mode: {args.text_mode}")
    logger.info(f"Frontend: http://localhost:3000")
    logger.info("=" * 60)

    if args.text_mode:
        logger.info("Text mode not implemented in simplified version")
        logger.info("Please use the web interface at http://localhost:3000")
        return

    try:
        # Run the server
        asyncio.run(
            run_server(
                profile_name=args.profile,
                region=args.region,
                host=args.host,
                port=args.port,
            )
        )
    except KeyboardInterrupt:
        logger.info("Voice assistant stopped by user")
    except Exception as e:
        logger.error(f"Voice assistant failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
