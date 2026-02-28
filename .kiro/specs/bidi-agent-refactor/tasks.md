# Implementation Plan: BidiAgent Refactor

## Overview

Refactor the voice-based AWS assistant from a multi-hop architecture (Nova Sonic → SupervisorAgent → specialized Haiku agents) to a single-hop architecture using Strands Agents' BidiAgent with the use_aws tool. Implementation proceeds bottom-up: update config, create I/O channels, rewrite server, update frontend, remove obsolete files, and update dependencies.

## Tasks

- [x] 1. Update backend configuration and model factory
  - [x] 1.1 Rewrite `backend/src/voice_based_aws_agent/config/config.py` with `AgentConfig` dataclass and `create_bidi_model()` factory
    - Define `AgentConfig` dataclass with fields: `region` (default `"us-east-1"`), `profile_name` (default `None`), `voice_id` (default `"matthew"`), `input_sample_rate` (default `16000`), `output_sample_rate` (default `24000`), `audio_channels` (default `1`), `audio_format` (default `"pcm"`)
    - Implement `create_bidi_model(config: AgentConfig) -> BidiNovaSonicModel` that creates a boto3 Session with the config's profile and region, then returns a `BidiNovaSonicModel` with model ID `amazon.nova-sonic-v1:0`, `provider_config` audio section matching all config fields, and `client_config` with the boto3 session and region
    - Remove `VoiceConfig`, `create_bedrock_model`, Claude Haiku model_id default, and `BedrockModel` import
    - _Requirements: 1.2, 5.1, 5.2, 5.3, 6.3, 6.4_

  - [ ]* 1.2 Write property test for `create_bidi_model()` configuration preservation
    - **Property 1: Model configuration preserves all AgentConfig parameters**
    - Generate random `AgentConfig` instances (varying profile, region, voice_id, sample rates, channels, format) using `hypothesis`
    - Call `create_bidi_model()` and verify the returned model's `provider_config` audio section matches the config's voice_id, input/output sample rates, channels, and format, and `client_config` contains a boto3 Session with the specified profile and region
    - Tag: `# Feature: bidi-agent-refactor, Property 1: Model configuration preserves all AgentConfig parameters`
    - **Validates: Requirements 1.2, 5.1, 6.3**

- [x] 2. Implement BidiAgent I/O channels
  - [x] 2.1 Create `backend/src/voice_based_aws_agent/utils/voice_integration/bidi_channels.py` with `WebSocketBidiInput` and `WebSocketBidiOutput`
    - Implement `WebSocketBidiInput(BidiInput)` with `__init__(websocket)`, `start(agent)`, `__call__() -> BidiInputEvent`, `stop()`, and `_read_loop()` methods
    - `_read_loop` reads JSON from WebSocket: `bidi_audio_input` → `BidiAudioInputEvent`, `bidi_text_input` → `BidiTextInputEvent`, `close` → stop signal
    - Handle `ConnectionClosed` in `_read_loop` to signal agent stop
    - Handle `JSONDecodeError` by logging warning and skipping invalid messages
    - Implement `WebSocketBidiOutput(BidiOutput)` with `__init__(websocket)`, `start(agent)`, `__call__(event)`, `stop()`, and `_serialize_event(event)` methods
    - `_serialize_event` maps each `BidiOutputEvent` type to JSON per the design's event table (audio_stream, transcript_stream, connection_start, connection_close, connection_restart, interruption, response_start, response_complete, error)
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 9.1_

  - [ ]* 2.2 Write property test for input channel message transformation
    - **Property 2: Input channel correctly transforms all frontend message types**
    - Generate random base64 audio data and text strings using `hypothesis`
    - Feed `bidi_audio_input` and `bidi_text_input` messages through `WebSocketBidiInput` and verify correct `BidiAudioInputEvent` / `BidiTextInputEvent` output with matching data
    - Tag: `# Feature: bidi-agent-refactor, Property 2: Input channel correctly transforms all frontend message types`
    - **Validates: Requirements 2.1, 2.3**

  - [ ]* 2.3 Write property test for output channel serialization
    - **Property 3: Output channel serializes all BidiOutputEvent types to valid JSON**
    - Generate random `BidiOutputEvent` instances of each type with random payloads using `hypothesis`
    - Pass through `WebSocketBidiOutput._serialize_event()` and verify JSON output has correct `type` field and all payload fields preserved
    - Tag: `# Feature: bidi-agent-refactor, Property 3: Output channel serializes all BidiOutputEvent types to valid JSON`
    - **Validates: Requirements 2.2, 2.4, 2.5, 2.6**

  - [ ]* 2.4 Write unit tests for I/O channel edge cases
    - Test WebSocket disconnect signals stop (simulate `ConnectionClosed` in `_read_loop`, verify agent receives stop signal)
    - Test invalid JSON from frontend is skipped with warning log
    - Test cleanup: verify `stop()` cancels the reader task
    - _Requirements: 2.7, 9.3_

- [x] 3. Consolidate system prompt and rewrite server
  - [x] 3.1 Create `build_system_prompt()` function in `server.py`
    - Consolidate instructions from EC2Agent, SSMAgent, BackupAgent prompts into a single prompt
    - Include the dangerous operation consent protocol from `prompt_consent.py`'s `get_consent_instructions()`
    - Add voice output guidelines (concise, no markdown, suitable for speech)
    - Add non-AWS query rejection instructions
    - _Requirements: 3.1, 3.2, 3.3, 3.4_

  - [x] 3.2 Rewrite `backend/src/voice_based_aws_agent/utils/voice_integration/server.py` with BidiAgent WebSocket handler
    - Implement `websocket_handler(websocket, path, profile_name, region)` that:
      1. Waits for optional `config` message from frontend (with timeout), extracts `voice_id` or defaults to `"matthew"`
      2. Sets `BYPASS_TOOL_CONSENT=true` environment variable
      3. Creates `AgentConfig` and `BidiNovaSonicModel` via `create_bidi_model()`
      4. Creates `BidiAgent(model=model, tools=[use_aws], system_prompt=build_system_prompt())`
      5. Creates `WebSocketBidiInput(websocket)` and `WebSocketBidiOutput(websocket)`
      6. Calls `await agent.run(inputs=[bidi_input], outputs=[bidi_output])`
      7. On exception, sends `bidi_error` event to frontend
      8. In `finally` block, calls `bidi_input.stop()` and `bidi_output.stop()`
    - Implement `run_server(profile_name, region, port)` to start the WebSocket server
    - _Requirements: 1.1, 1.3, 1.4, 1.5, 5.4, 6.4, 9.1, 9.2, 9.3_

  - [ ]* 3.3 Write property test for error forwarding
    - **Property 5: Errors are forwarded as bidi_error events**
    - Generate random exceptions with random messages using `hypothesis`
    - Verify the error handling path produces a JSON message with `type` equal to `bidi_error` and a non-empty `message` field
    - Tag: `# Feature: bidi-agent-refactor, Property 5: Errors are forwarded as bidi_error events`
    - **Validates: Requirements 9.1**

  - [ ]* 3.4 Write unit tests for server and system prompt
    - Test `AgentConfig()` defaults: region `"us-east-1"`, voice_id `"matthew"`, sample rates 16000/24000
    - Test voice ID defaults to `"matthew"` when no config message received from frontend
    - Test `build_system_prompt()` contains EC2/SSM/Backup instructions, consent protocol, voice guidelines, and non-AWS rejection
    - Test connection failure sends `bidi_error` and closes WebSocket cleanly
    - Test cleanup on disconnect: verify `bidi_input.stop()` and `bidi_output.stop()` are called
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 6.4, 9.2, 9.3_

- [x] 4. Checkpoint - Backend core implementation
  - Ensure all tests pass, ask the user if questions arise.

- [x] 5. Simplify backend entry point
  - [x] 5.1 Rewrite `backend/src/voice_based_aws_agent/main.py`
    - Remove orchestrator initialization and multi-agent setup
    - Parse CLI args (`--profile`, `--region`, `--port`, `--voice`) using argparse
    - Call `run_server(profile_name, region, port)` directly
    - Keep `--voice` arg as fallback default only (frontend voice selection takes precedence)
    - _Requirements: 5.2, 5.3_

- [x] 6. Create frontend BidiEvent helpers
  - [x] 6.1 Create `frontend/src/helper/BidiEventHelpers.js`
    - Export `BidiEventHelpers` object with methods: `audioInput(base64Data)`, `textInput(text)`, `config(voiceId)`, `close()`
    - Each method returns the correctly structured JSON message per the design's frontend→backend message table
    - _Requirements: 4.1, 4.6_

- [x] 7. Update frontend VoiceAgent
  - [x] 7.1 Rewrite WebSocket connection and message handling in `frontend/src/VoiceAgent.js`
    - **`connectWebSocket()`**: On open, send `config` message with selected voice_id via `BidiEventHelpers.config()`. Remove `sessionStart`, `promptStart`, `contentStartText`, `textInput`, `contentEnd`, `contentStartAudio` event sequence
    - **`startMicrophone()`**: Send audio chunks as `bidi_audio_input` events via `BidiEventHelpers.audioInput()` instead of raw `audioInput` events with `promptName`/`contentName`
    - **`handleIncomingMessage()`**: Switch on `message.type` to handle: `bidi_audio_stream` (decode and play audio), `bidi_transcript_stream` (display transcript with correct role), `bidi_interruption` (call `audioPlayer.bargeIn()`), `bidi_connection_start`, `bidi_connection_close` (display disconnection, reset state), `bidi_connection_restart`, `bidi_response_start`, `bidi_response_complete`, `bidi_error` (display alert banner with "Restart Conversation" button)
    - **`endSession()`**: Send `close` event via `BidiEventHelpers.close()` instead of `sessionEnd`, stop microphone capture
    - Remove `promptName`, `textContentName`, `audioContentName` state variables
    - Remove `supervisorAgent` tool configuration from session setup
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7, 6.1, 6.2, 9.4_

  - [ ]* 7.2 Write property test for transcript display (fast-check)
    - **Property 4: Transcript events are displayed with the correct role**
    - Generate random `bidi_transcript_stream` messages with random roles ("user"/"assistant") and text using `fast-check`
    - Verify the chat message handler produces entries with matching role and text content
    - Tag: `// Feature: bidi-agent-refactor, Property 4: Transcript events are displayed with the correct role`
    - **Validates: Requirements 4.3**

  - [ ]* 7.3 Write unit tests for frontend event handling
    - Test `bidi_error` event triggers alert banner with "Restart Conversation" button
    - Test `bidi_interruption` event calls `audioPlayer.bargeIn()`
    - Test `bidi_connection_close` event displays disconnection message and resets state
    - Test ending session sends `close` event and stops microphone
    - _Requirements: 4.4, 4.5, 4.6, 9.4_

- [x] 8. Checkpoint - Frontend implementation
  - Ensure all tests pass, ask the user if questions arise.

- [x] 9. Remove obsolete multi-agent components
  - [x] 9.1 Delete obsolete backend files
    - Delete `backend/src/voice_based_aws_agent/utils/voice_integration/s2s_session_manager.py` (replaced by BidiAgent)
    - Delete `backend/src/voice_based_aws_agent/utils/voice_integration/s2s_events.py` (BidiAgent manages events)
    - Delete `backend/src/voice_based_aws_agent/utils/voice_integration/supervisor_agent_integration.py` (integration layer removed)
    - Delete `backend/src/voice_based_aws_agent/agents/supervisor_agent.py` (routing eliminated)
    - Delete `backend/src/voice_based_aws_agent/agents/orchestrator.py` (orchestration eliminated)
    - Delete `backend/src/voice_based_aws_agent/agents/ec2_agent.py` (BidiAgent handles directly)
    - Delete `backend/src/voice_based_aws_agent/agents/ssm_agent.py` (BidiAgent handles directly)
    - Delete `backend/src/voice_based_aws_agent/agents/backup_agent.py` (BidiAgent handles directly)
    - Delete `backend/tools/supervisor_tool.py` (bridge no longer needed)
    - Delete `backend/src/voice_based_aws_agent/config/conversation_config.py` (BidiAgent manages context)
    - Delete `frontend/src/helper/s2sEvents.js` (replaced by `BidiEventHelpers.js`)
    - Update `__init__.py` files to remove imports of deleted modules
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 7.7, 7.8_

- [x] 10. Update project dependencies
  - [x] 10.1 Update `requirements.txt` and `pyproject.toml`
    - Add `strands-agents[bidi]` dependency
    - Remove `aws-sdk-bedrock-runtime` and `smithy-aws-core` dependencies
    - Remove `rx` dependency
    - Remove `pyaudio` dependency
    - _Requirements: 8.1, 8.2, 8.3, 8.4_

- [x] 11. Final checkpoint - Full integration
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests use `hypothesis` (Python) and `fast-check` (JavaScript)
- Unit tests validate specific examples and edge cases
- Backend implementation (tasks 1-5) should be completed before frontend (tasks 6-7) to enable integration testing
- File deletion (task 9) is done after both backend and frontend are working to avoid breaking the existing system during development
