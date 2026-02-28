# Requirements Document

## Introduction

This document specifies the requirements for refactoring the voice-based AWS assistant from a multi-hop architecture (Nova Sonic → SupervisorAgent → specialized Claude Haiku agents) to a single-hop architecture using Strands Agents' BidiAgent. The refactor eliminates two intermediate Claude Haiku LLM hops that add latency to voice conversations, replacing them with a BidiAgent that natively handles speech-to-text, tool execution, and text-to-speech in a single bidirectional stream.

## Glossary

- **BidiAgent**: A Strands Agents experimental class (`strands.experimental.bidi.BidiAgent`) that manages a bidirectional audio stream with built-in speech-to-text, reasoning, tool execution, and text-to-speech capabilities.
- **BidiNovaSonicModel**: The model adapter (`strands.experimental.bidi.models.BidiNovaSonicModel`) that connects BidiAgent to Amazon Nova Sonic (model ID `amazon.nova-sonic-v1:0`).
- **BidiInput**: A callable protocol for providing input events (audio or text) to a BidiAgent session.
- **BidiOutput**: A callable protocol for receiving output events (audio, transcripts, lifecycle) from a BidiAgent session.
- **BidiOutputEvent**: An event emitted by BidiAgent, including types such as `bidi_audio_stream`, `bidi_transcript_stream`, `bidi_connection_start`, `bidi_connection_close`, `bidi_interruption`, `bidi_response_start`, and `bidi_response_complete`.
- **WebSocket_Server**: The backend Python WebSocket server that bridges the frontend browser to the BidiAgent.
- **Frontend**: The React-based web application that captures microphone audio, sends it over WebSocket, and plays back audio responses.
- **use_aws**: The Strands tool (`strands_tools.use_aws`) that executes AWS CLI API calls for EC2, SSM, Backup, and other AWS services.
- **S2sSessionManager**: The existing custom session manager class that manually manages the low-level Bedrock bidirectional stream, to be replaced by BidiAgent.
- **SupervisorAgent**: The existing routing agent (Claude 3 Haiku) that keyword-routes queries to specialized agents, to be eliminated.
- **Specialized_Agent**: The existing EC2Agent, SSMAgent, and BackupAgent classes (each using Claude 3 Haiku + use_aws), to be eliminated as separate entities.

## Requirements

### Requirement 1: Replace S2sSessionManager with BidiAgent

**User Story:** As a developer, I want to replace the custom S2sSessionManager with Strands BidiAgent, so that bidirectional stream management, tool orchestration, and audio processing are handled by the framework rather than custom code.

#### Acceptance Criteria

1. WHEN a WebSocket connection is established, THE WebSocket_Server SHALL create a BidiAgent instance configured with a BidiNovaSonicModel and the use_aws tool.
2. THE BidiAgent SHALL be configured with model ID `amazon.nova-sonic-v1:0`, input sample rate 16000 Hz, output sample rate 24000 Hz, PCM format, 1 channel, and a configurable voice ID.
3. THE BidiAgent SHALL receive the use_aws tool directly in its tools list, enabling single-hop tool execution without intermediate agent routing.
4. WHEN the BidiAgent session starts, THE WebSocket_Server SHALL invoke `agent.run()` with custom BidiInput and BidiOutput channel implementations that bridge to the frontend WebSocket.
5. WHEN the WebSocket connection closes, THE WebSocket_Server SHALL stop the BidiAgent session and release all associated resources.

### Requirement 2: Implement Custom WebSocket-to-BidiAgent I/O Channels

**User Story:** As a developer, I want custom I/O channel classes that bridge the frontend WebSocket to BidiAgent's input/output protocols, so that browser audio flows seamlessly through the BidiAgent pipeline.

#### Acceptance Criteria

1. THE WebSocket_Server SHALL implement a BidiInput-compatible class that reads audio data from the frontend WebSocket and returns BidiAudioInputEvent instances to the BidiAgent.
2. THE WebSocket_Server SHALL implement a BidiOutput-compatible class that receives BidiOutputEvent instances from the BidiAgent and forwards them as JSON messages over the frontend WebSocket.
3. WHEN the BidiInput channel receives a text message from the frontend WebSocket, THE BidiInput channel SHALL return a BidiTextInputEvent to the BidiAgent.
4. WHEN the BidiOutput channel receives a `bidi_audio_stream` event, THE BidiOutput channel SHALL forward the audio data to the frontend WebSocket as a JSON message.
5. WHEN the BidiOutput channel receives a `bidi_transcript_stream` event, THE BidiOutput channel SHALL forward the transcript data to the frontend WebSocket as a JSON message.
6. WHEN the BidiOutput channel receives lifecycle events (`bidi_connection_start`, `bidi_connection_close`, `bidi_response_start`, `bidi_response_complete`, `bidi_interruption`), THE BidiOutput channel SHALL forward each event to the frontend WebSocket as a JSON message.
7. IF the frontend WebSocket disconnects unexpectedly, THEN THE BidiInput channel SHALL signal the BidiAgent to stop by raising a StopIteration or returning a close event.

### Requirement 3: Consolidate System Prompt for Single-Agent Architecture

**User Story:** As a developer, I want a comprehensive system prompt for the BidiAgent that covers all AWS service domains (EC2, SSM, Backup), so that the single agent can handle all query types without a routing layer.

#### Acceptance Criteria

1. THE BidiAgent SHALL be configured with a system prompt that includes instructions for handling EC2, SSM, and Backup operations using the use_aws tool.
2. THE BidiAgent system prompt SHALL include the dangerous operation consent protocol currently defined in the prompt_consent module, requiring explicit user confirmation before executing destructive AWS operations.
3. THE BidiAgent system prompt SHALL instruct the agent to keep responses concise and suitable for voice output.
4. THE BidiAgent system prompt SHALL instruct the agent to reject non-AWS queries and redirect users to AWS-related topics.

### Requirement 4: Update Frontend WebSocket Protocol

**User Story:** As a user, I want the frontend to communicate using the BidiAgent event format, so that I can have voice conversations with the refactored backend.

#### Acceptance Criteria

1. WHEN the user starts a conversation, THE Frontend SHALL establish a WebSocket connection to the backend and begin sending audio data in a format compatible with the BidiInput channel.
2. WHEN the Frontend receives a `bidi_audio_stream` event from the WebSocket, THE Frontend SHALL decode the audio data and play it through the AudioPlayer.
3. WHEN the Frontend receives a `bidi_transcript_stream` event from the WebSocket, THE Frontend SHALL display the transcript text in the chat area with the correct role (user or assistant).
4. WHEN the Frontend receives a `bidi_interruption` event, THE Frontend SHALL cancel current audio playback by calling the AudioPlayer barge-in method.
5. WHEN the Frontend receives a `bidi_connection_close` event, THE Frontend SHALL display a disconnection message and reset the session state.
6. WHEN the user ends a conversation, THE Frontend SHALL send a close signal over the WebSocket and stop microphone capture.
7. THE Frontend SHALL remove the supervisorAgent tool configuration from the session setup, as tool management is handled internally by the BidiAgent.

### Requirement 5: Preserve AWS Authentication Configuration

**User Story:** As a developer, I want AWS authentication to work with the BidiNovaSonicModel, so that the agent can access AWS services using the configured profile and region.

#### Acceptance Criteria

1. THE WebSocket_Server SHALL pass a boto3 Session configured with the specified AWS profile and region to the BidiNovaSonicModel via the `client_config` parameter.
2. WHEN the `--profile` command-line argument is provided, THE WebSocket_Server SHALL use the specified profile for the boto3 Session.
3. WHEN the `--region` command-line argument is provided, THE WebSocket_Server SHALL use the specified region for the BidiNovaSonicModel client configuration.
4. THE WebSocket_Server SHALL set the `BYPASS_TOOL_CONSENT` environment variable to `true` before creating the BidiAgent, ensuring the use_aws tool operates without interactive prompts.

### Requirement 6: Preserve Voice Configuration Options

**User Story:** As a user, I want to select my preferred voice and have it applied to the BidiAgent, so that the assistant responds in my chosen voice.

#### Acceptance Criteria

1. THE Frontend SHALL provide a voice selection dropdown with options for "matthew", "tiffany", and "amy".
2. WHEN the user selects a voice and starts a conversation, THE Frontend SHALL send the selected voice ID to the backend as part of the connection setup.
3. WHEN the WebSocket_Server receives a voice ID from the frontend, THE WebSocket_Server SHALL configure the BidiNovaSonicModel `provider_config` audio section with the specified voice ID.
4. IF no voice ID is provided by the frontend, THEN THE WebSocket_Server SHALL default to the "matthew" voice ID.

### Requirement 7: Remove Obsolete Multi-Agent Components

**User Story:** As a developer, I want to remove the obsolete multi-agent routing code, so that the codebase is clean and maintainable.

#### Acceptance Criteria

1. THE codebase SHALL remove the S2sSessionManager class (`s2s_session_manager.py`), as its functionality is replaced by BidiAgent.
2. THE codebase SHALL remove the SupervisorAgent class (`supervisor_agent.py`), as query routing is no longer needed.
3. THE codebase SHALL remove the AgentOrchestrator class (`orchestrator.py`), as multi-agent orchestration is no longer needed.
4. THE codebase SHALL remove the specialized agent classes EC2Agent (`ec2_agent.py`), SSMAgent (`ssm_agent.py`), and BackupAgent (`backup_agent.py`), as the BidiAgent handles all domains directly.
5. THE codebase SHALL remove the supervisor_tool module (`supervisor_tool.py`), as the bridge between Nova Sonic tool calls and the orchestrator is no longer needed.
6. THE codebase SHALL remove the SupervisorAgentIntegration class (`supervisor_agent_integration.py`), as the integration layer is no longer needed.
7. THE codebase SHALL remove the S2sEvent class (`s2s_events.py`), as BidiAgent manages its own event protocol.
8. THE codebase SHALL remove the ConversationConfig module (`conversation_config.py`), as BidiAgent manages conversation context internally.

### Requirement 8: Update Dependencies

**User Story:** As a developer, I want the project dependencies updated to include the BidiAgent extras and remove unused packages, so that the project builds correctly with minimal dependencies.

#### Acceptance Criteria

1. THE `pyproject.toml` and `requirements.txt` SHALL include `strands-agents[bidi]` as a dependency to enable BidiAgent support.
2. THE `pyproject.toml` and `requirements.txt` SHALL remove the `aws-sdk-bedrock-runtime` and `smithy-aws-core` dependencies, as the low-level Bedrock SDK is no longer used directly.
3. THE `pyproject.toml` and `requirements.txt` SHALL remove the `rx` dependency, as reactive extensions are no longer used.
4. THE `pyproject.toml` and `requirements.txt` SHALL remove the `pyaudio` dependency, as server-side audio capture is not used (audio is captured by the browser).

### Requirement 9: Error Handling and Connection Resilience

**User Story:** As a user, I want the voice assistant to handle errors gracefully, so that I receive clear feedback when something goes wrong.

#### Acceptance Criteria

1. IF the BidiAgent encounters an error during tool execution, THEN THE WebSocket_Server SHALL forward an error event to the frontend with a descriptive message.
2. IF the BidiNovaSonicModel fails to establish a connection, THEN THE WebSocket_Server SHALL send an error event to the frontend and close the WebSocket connection cleanly.
3. IF the frontend WebSocket disconnects during an active BidiAgent session, THEN THE WebSocket_Server SHALL stop the BidiAgent session within 5 seconds and release all resources.
4. WHEN the Frontend receives an error event from the WebSocket, THE Frontend SHALL display the error message in an alert banner with a "Restart Conversation" option.
