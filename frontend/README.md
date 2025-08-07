# Voice-Based AWS Agent React Client

This is the React client for the Voice-Based AWS Agent project. It provides a web interface to interact with the voice-based AI assistant using Amazon Nova Sonic.

## Features

- Real-time voice communication with AWS services
- Text transcript of conversations
- Event monitoring for debugging
- Support for different voice options (Matthew, Tiffany, Amy)
- WebSocket connection to the Python backend

## Prerequisites

- Node.js 14.x or higher
- npm 6.x or higher
- Running Python WebSocket server from the main project

## Installation

1. Install dependencies:

```bash
cd react-client
npm install
```

2. Start the development server:

```bash
npm start
```

The application will be available at http://localhost:3000

## Usage

1. Ensure the Python WebSocket server is running:

```bash
# From the project root
python -m src.voice_based_aws_agent.main
```

2. In the React client:
   - Verify the WebSocket URL (default: ws://localhost:8080)
   - Select your preferred voice
   - Click "Start Conversation" to begin
   - Speak into your microphone to interact with the AWS agent
   - Click "End Conversation" when finished

## Configuration

- **WebSocket URL**: The URL of the Python WebSocket server
- **Voice**: Select from available Amazon Nova Sonic voices (Matthew, Tiffany, Amy)

## Troubleshooting

If you encounter issues:

1. Check that the Python WebSocket server is running
2. Ensure your browser has permission to access your microphone
3. Verify that your AWS credentials are properly configured in the Python backend
4. Check the browser console for any error messages

## License

This project is licensed under the MIT License - see the LICENSE file for details.
