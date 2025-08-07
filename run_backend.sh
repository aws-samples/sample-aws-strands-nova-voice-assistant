#!/bin/bash

# Activate virtual environment if it exists
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Add the project root to PYTHONPATH
export PYTHONPATH=$PYTHONPATH:$(pwd)

# Set BYPASS_TOOL_CONSENT to skip interactive prompts (essential for voice agents)
export BYPASS_TOOL_CONSENT=true

echo "🔧 BYPASS_TOOL_CONSENT is set to: $BYPASS_TOOL_CONSENT"
echo "🚀 Starting Voice-based AWS Agent..."

# Run the backend server
cd backend
python -m src.voice_based_aws_agent.main "$@"
