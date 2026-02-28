#!/usr/bin/env python3
"""CLI entry point for the BidiAgent voice-based AWS assistant."""

import asyncio
import argparse
import logging
import os
import sys

from dotenv import load_dotenv

load_dotenv()

from .utils.voice_integration.server import run_server

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("VoiceAssistantMain")


def main():
    """Parse CLI arguments and start the BidiAgent WebSocket server."""
    parser = argparse.ArgumentParser(description="AWS BidiAgent Voice Assistant")
    parser.add_argument(
        "--profile",
        default=os.getenv("AWS_PROFILE", "default"),
        help="AWS profile name (default: AWS_PROFILE env var or 'default')",
    )
    parser.add_argument(
        "--region",
        default=os.getenv("AWS_DEFAULT_REGION", "us-east-1"),
        help="AWS region (default: us-east-1)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8080,
        help="WebSocket server port (default: 8080)",
    )
    parser.add_argument(
        "--voice",
        choices=["matthew", "tiffany", "amy"],
        default="matthew",
        help="Fallback voice ID if frontend does not specify one (default: matthew)",
    )

    args = parser.parse_args()

    logger.info("Starting BidiAgent Voice Assistant (profile=%s, region=%s, port=%s)",
                args.profile, args.region, args.port)

    try:
        asyncio.run(
            run_server(
                profile_name=args.profile,
                region=args.region,
                port=args.port,
            )
        )
    except KeyboardInterrupt:
        logger.info("Voice assistant stopped by user")
    except Exception as e:
        logger.error("Voice assistant failed: %s", e)
        sys.exit(1)


if __name__ == "__main__":
    main()
