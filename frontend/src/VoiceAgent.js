import React from 'react';
import './VoiceAgent.css';
import { 
    Alert, 
    Button, 
    SpaceBetween, 
    Container, 
    ColumnLayout, 
    Header, 
    FormField, 
    Select, 
    Checkbox,
    Grid
} from '@cloudscape-design/components';
import S2sEvent from './helper/s2sEvents';
import EventDisplay from './components/EventDisplay';
import { base64ToFloat32Array } from './helper/audioHelper';
import AudioPlayer from './helper/audioPlayer';

class VoiceAgent extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            status: "loading", // null, loading, loaded
            alert: null,
            sessionStarted: false,
            showEventJson: false,
            showConfig: false,
            selectedEvent: null,

            chatMessages: {},
            events: [],
            audioChunks: [],
            audioPlayPromise: null,
            includeChatHistory: false,

            promptName: null,
            textContentName: null,
            audioContentName: null,

            // S2S config items
            configAudioInput: null,
            configSystemPrompt: S2sEvent.DEFAULT_SYSTEM_PROMPT,
            configAudioOutput: S2sEvent.DEFAULT_AUDIO_OUTPUT_CONFIG,
            configVoiceIdOption: { label: "Matthew (en-US)", value: "matthew" },
            websocketUrl: "ws://localhost:8080"
        };
        
        // Audio processing limits for security
        this.MAX_AUDIO_CHUNK_SIZE = 64 * 1024; // 64KB max per chunk
        this.MAX_AUDIO_BUFFER_SIZE = 1024 * 1024; // 1MB max total buffer
        this.audioBufferSize = 0;
        
        this.socket = null;
        this.mediaRecorder = null;
        this.chatMessagesEndRef = React.createRef();
        this.stateRef = React.createRef();
        this.eventDisplayRef = React.createRef();
        this.audioPlayer = new AudioPlayer();
    }

    componentDidMount() {
        this.stateRef.current = this.state;
        // Initialize audio player early
        this.audioPlayer.start().catch(err => {
            console.error("Failed to initialize audio player:", err);
        });
        
        // Set status to loaded for localhost development
        this.setState({ status: "loaded" });
    }

    componentWillUnmount() {
        this.audioPlayer.stop();
    }

    componentDidUpdate(prevProps, prevState) {
        this.stateRef.current = this.state;

        if (Object.keys(prevState.chatMessages).length !== Object.keys(this.state.chatMessages).length) {
            this.chatMessagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
        }
    }

    sendEvent(event) {
        if (this.socket && this.socket.readyState === WebSocket.OPEN) {
            this.socket.send(JSON.stringify(event));
            event.timestamp = Date.now();

            if (this.eventDisplayRef.current) {
                this.eventDisplayRef.current.displayEvent(event, "out");
            }
        }
    }

    cancelAudio() {
        this.audioPlayer.bargeIn();
        this.setState({ isPlaying: false });
    }

    handleIncomingMessage(message) {
        const eventType = Object.keys(message?.event)[0];
        const role = message.event[eventType]["role"];
        const content = message.event[eventType]["content"];
        const contentId = message.event[eventType].contentId;
        let stopReason = message.event[eventType].stopReason;
        const contentType = message.event[eventType].type;
        var chatMessages = this.state.chatMessages;

        switch(eventType) {
            case "textOutput": 
                // Detect interruption
                if (role === "ASSISTANT" && content && content.startsWith("{")) {
                    try {
                        const evt = JSON.parse(content);
                        if (evt.interrupted === true) {
                            this.cancelAudio();
                        }
                    } catch (e) {
                        // Not JSON, continue normally
                    }
                }

                if (chatMessages.hasOwnProperty(contentId)) {
                    chatMessages[contentId].content = content;
                    chatMessages[contentId].role = role;
                    if (chatMessages[contentId].raw === undefined)
                        chatMessages[contentId].raw = [];
                    chatMessages[contentId].raw.push(message);
                }
                this.setState({chatMessages: chatMessages});
                break;
                
            case "audioOutput":
                try {
                    const base64Data = message.event[eventType].content;
                    
                    // Validate audio chunk size for security
                    const chunkSize = base64Data.length;
                    if (chunkSize > this.MAX_AUDIO_CHUNK_SIZE) {
                        console.warn(`Audio chunk size (${chunkSize}) exceeds maximum allowed (${this.MAX_AUDIO_CHUNK_SIZE}). Skipping chunk.`);
                        break;
                    }
                    
                    // Check total buffer size
                    this.audioBufferSize += chunkSize;
                    if (this.audioBufferSize > this.MAX_AUDIO_BUFFER_SIZE) {
                        console.warn(`Total audio buffer size (${this.audioBufferSize}) exceeds maximum allowed (${this.MAX_AUDIO_BUFFER_SIZE}). Resetting buffer.`);
                        this.audioBufferSize = chunkSize; // Reset to current chunk size
                    }
                    
                    const audioData = base64ToFloat32Array(base64Data);
                    this.audioPlayer.playAudio(audioData);
                } catch (error) {
                    console.error("Error processing audio chunk:", error);
                }
                break;
                
            case "contentStart":
                if (contentType === "TEXT") {
                    var generationStage = "";
                    if (message.event.contentStart.additionalModelFields) {
                        generationStage = JSON.parse(message.event.contentStart.additionalModelFields)?.generationStage;
                    }

                    chatMessages[contentId] = {
                        "content": "", 
                        "role": role,
                        "generationStage": generationStage,
                        "raw": [],
                    };
                    chatMessages[contentId].raw.push(message);
                    this.setState({chatMessages: chatMessages});
                }
                break;
                
            case "contentEnd":
                if (contentType === "TEXT") {
                    if (chatMessages.hasOwnProperty(contentId)) {
                        if (chatMessages[contentId].raw === undefined)
                            chatMessages[contentId].raw = [];
                        chatMessages[contentId].raw.push(message);
                        chatMessages[contentId].stopReason = stopReason;
                    }
                    this.setState({chatMessages: chatMessages});
                }
                break;
                
            case "streamRecovery":
                console.log("Stream recovery event:", message.event.streamRecovery.message);
                // Show a recovery message with restart option
                this.setState({
                    alert: {
                        type: "warning",
                        message: message.event.streamRecovery.message + " Please restart your conversation.",
                        dismissible: true,
                        showRestart: true
                    }
                });
                
                // Automatically end the current session to allow restart
                if (this.state.sessionStarted) {
                    this.endSession();
                    this.setState({ sessionStarted: false });
                }
                break;
                
            case "streamStatus":
                const status = message.event.streamStatus.status;
                const statusMessage = message.event.streamStatus.message;
                console.log("Stream status:", status, statusMessage);
                
                if (status === "reconnecting") {
                    this.setState({
                        alert: {
                            type: "info",
                            message: statusMessage,
                            dismissible: false
                        }
                    });
                } else if (status === "connected") {
                    this.setState({
                        alert: {
                            type: "success",
                            message: statusMessage,
                            dismissible: true,
                            showRestart: true
                        }
                    });
                    
                    // End current session to allow clean restart
                    if (this.state.sessionStarted) {
                        this.endSession();
                        this.setState({ sessionStarted: false });
                    }
                    
                    // Auto-dismiss success message after 5 seconds
                    setTimeout(() => {
                        this.setState({alert: null});
                    }, 5000);
                } else if (status === "error") {
                    this.setState({
                        alert: {
                            type: "error",
                            message: statusMessage,
                            dismissible: true
                        }
                    });
                    
                    // End current session on error
                    if (this.state.sessionStarted) {
                        this.endSession();
                        this.setState({ sessionStarted: false });
                    }
                }
                break;
                
            default:
                break;
        }

        if (this.eventDisplayRef.current) {
            this.eventDisplayRef.current.displayEvent(message, "in");
        }
    }

    handleSessionChange = e => {
        if (this.state.sessionStarted) {
            // End session
            this.endSession();
            this.cancelAudio();
            this.audioPlayer.start(); 
        } else {
            // Start session
            this.setState({
                chatMessages: {}, 
                events: [], 
            });
            if (this.eventDisplayRef.current) this.eventDisplayRef.current.cleanup();
            
            // Init S2sSessionManager
            try {
                if (this.socket === null || this.socket.readyState !== WebSocket.OPEN) {
                    this.connectWebSocket();
                }

                // Start microphone 
                this.startMicrophone();
            } catch (error) {
                console.error('Error accessing microphone: ', error);
                this.setState({alert: `Error accessing microphone: ${error.message}`});
            }
        }
        this.setState({sessionStarted: !this.state.sessionStarted});
    }

    connectWebSocket() {
        // Connect to the S2S WebSocket server
        if (this.socket === null || this.socket.readyState !== WebSocket.OPEN) {
            const promptName = crypto.randomUUID();
            const textContentName = crypto.randomUUID();
            const audioContentName = crypto.randomUUID();
            this.setState({
                promptName: promptName,
                textContentName: textContentName,
                audioContentName: audioContentName
            });

            this.socket = new WebSocket(this.state.websocketUrl);
            
            this.socket.onopen = () => {
                console.log("WebSocket connected!");
                this.setState({status: "connected"});

                // Start session events
                this.sendEvent(S2sEvent.sessionStart());

                var audioConfig = S2sEvent.DEFAULT_AUDIO_OUTPUT_CONFIG;
                audioConfig.voiceId = this.state.configVoiceIdOption.value;

                // Create tool configuration for supervisor agent
                const toolConfig = {
                    "tools": [
                        {
                            "toolSpec": {
                                "name": "supervisorAgent",
                                "description": "Routes queries to specialized agents for EC2, Backup, and SSM",
                                "inputSchema": {
                                    "json": JSON.stringify({
                                        "$schema": "http://json-schema.org/draft-07/schema#",
                                        "type": "object",
                                        "properties": {
                                            "query": {
                                                "type": "string",
                                                "description": "The user query about AWS services or operations"
                                            }
                                        },
                                        "required": ["query"]
                                    })
                                }
                            }
                        }
                    ]
                };

                this.sendEvent(S2sEvent.promptStart(promptName, audioConfig, toolConfig));

                this.sendEvent(S2sEvent.contentStartText(promptName, textContentName));
                this.sendEvent(S2sEvent.textInput(promptName, textContentName, this.state.configSystemPrompt));
                this.sendEvent(S2sEvent.contentEnd(promptName, textContentName));

                // Chat history (if enabled)
                if (this.state.includeChatHistory) {
                    // Add any chat history logic here if needed
                }

                this.sendEvent(S2sEvent.contentStartAudio(promptName, audioContentName));
            };

            // Handle incoming messages
            this.socket.onmessage = (message) => {
                const event = JSON.parse(message.data);
                this.handleIncomingMessage(event);
            };

            // Handle errors
            this.socket.onerror = (error) => {
                console.error("WebSocket Error: ", error);
                this.setState({
                    status: "disconnected",
                    alert: {
                        type: "error",
                        message: "WebSocket connection error. Please restart your conversation.",
                        dismissible: true,
                        showRestart: true
                    }
                });
                
                // End session on WebSocket error
                if (this.state.sessionStarted) {
                    this.endSession();
                    this.setState({ sessionStarted: false });
                }
            };

            // Handle connection close
            this.socket.onclose = (event) => {
                console.log("WebSocket Disconnected", event.code, event.reason);
                this.setState({status: "disconnected"});
                
                // Show appropriate message based on close code
                if (event.code === 1005) {
                    // No status code - likely a connection drop
                    this.setState({
                        alert: {
                            type: "warning",
                            message: "Connection lost unexpectedly. Please restart your conversation.",
                            dismissible: true,
                            showRestart: true
                        }
                    });
                } else if (event.code !== 1000) {
                    // Abnormal closure
                    this.setState({
                        alert: {
                            type: "error",
                            message: `Connection closed unexpectedly (${event.code}). Please restart your conversation.`,
                            dismissible: true,
                            showRestart: true
                        }
                    });
                }
                
                // End session on WebSocket close
                if (this.state.sessionStarted) {
                    this.endSession();
                    this.setState({ sessionStarted: false });
                }
            };
        }
    }

    async startMicrophone() {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({
                audio: {
                    echoCancellation: true,
                    noiseSuppression: true,
                    autoGainControl: true
                }
            });

            const audioContext = new (window.AudioContext || window.webkitAudioContext)({
                latencyHint: 'interactive'
            });

            const source = audioContext.createMediaStreamSource(stream);
            const processor = audioContext.createScriptProcessor(512, 1, 1);

            source.connect(processor);
            processor.connect(audioContext.destination);

            const targetSampleRate = 16000;

            processor.onaudioprocess = async (e) => {
                if (this.state.sessionStarted) {
                    const inputBuffer = e.inputBuffer;

                    // Create an offline context for resampling
                    const offlineContext = new OfflineAudioContext({
                        numberOfChannels: 1,
                        length: Math.ceil(inputBuffer.duration * targetSampleRate),
                        sampleRate: targetSampleRate
                    });

                    // Copy and resample the audio data
                    const offlineBuffer = offlineContext.createBuffer(1, offlineContext.length, targetSampleRate);
                    const inputData = inputBuffer.getChannelData(0);
                    const outputData = offlineBuffer.getChannelData(0);

                    // Simple resampling
                    const ratio = inputBuffer.sampleRate / targetSampleRate;
                    for (let i = 0; i < outputData.length; i++) {
                        const srcIndex = Math.floor(i * ratio);
                        if (srcIndex < inputData.length) {
                            outputData[i] = inputData[srcIndex];
                        }
                    }

                    // Convert to base64
                    const pcmData = new Int16Array(outputData.length);
                    for (let i = 0; i < outputData.length; i++) {
                        pcmData[i] = Math.max(-32768, Math.min(32767, outputData[i] * 32768));
                    }

                    const base64Data = btoa(String.fromCharCode(...new Uint8Array(pcmData.buffer)));

                    // Validate input audio chunk size for security
                    if (base64Data.length > this.MAX_AUDIO_CHUNK_SIZE) {
                        console.warn(`Input audio chunk size (${base64Data.length}) exceeds maximum allowed (${this.MAX_AUDIO_CHUNK_SIZE}). Skipping chunk.`);
                        return;
                    }

                    // Send audio data
                    this.sendEvent(S2sEvent.audioInput(this.state.promptName, this.state.audioContentName, base64Data));
                }
            };

            this.mediaRecorder = { processor, stream };
        } catch (error) {
            console.error('Error accessing microphone:', error);
            throw error;
        }
    }

    endSession() {
        // Stop microphone first
        if (this.mediaRecorder) {
            if (this.mediaRecorder.processor) {
                this.mediaRecorder.processor.disconnect();
            }
            if (this.mediaRecorder.stream) {
                this.mediaRecorder.stream.getTracks().forEach(track => track.stop());
            }
            this.mediaRecorder = null;
        }

        // Close WebSocket if it's open and connected
        if (this.socket && this.socket.readyState === WebSocket.OPEN) {
            try {
                // Only send close events if the connection is still good
                if (this.state.promptName) {
                    this.sendEvent(S2sEvent.contentEnd(this.state.promptName, this.state.audioContentName));
                    this.sendEvent(S2sEvent.promptEnd(this.state.promptName));
                }
                this.sendEvent(S2sEvent.sessionEnd());
            } catch (error) {
                console.warn("Error sending close events:", error);
            }
            
            // Close the socket
            this.socket.close();
        }

        // Clean up socket reference
        this.socket = null;
        
        // Reset audio buffer size for security
        this.audioBufferSize = 0;
        
        // Update state
        this.setState({ 
            sessionStarted: false, 
            status: "disconnected",
            promptName: null,
            textContentName: null,
            audioContentName: null
        });
        
        console.log('Session ended and cleaned up');
    }

    renderChatMessages() {
        const messages = Object.values(this.state.chatMessages).sort((a, b) => {
            return (a.raw[0]?.timestamp || 0) - (b.raw[0]?.timestamp || 0);
        });

        return messages.map((message, index) => {
            const isUser = message.role === "USER";
            const isAssistant = message.role === "ASSISTANT";
            
            if (!isUser && !isAssistant) return null;

            return (
                <div key={index} className={`chat-item ${isUser ? 'user' : 'bot'}`}>
                    <div className={`message-bubble ${isUser ? 'user-message' : 'bot-message'}`}>
                        {message.content || (isAssistant && message.generationStage ? 
                            <div className="loading-bubble">
                                <div className="loading-dots">
                                    <span></span>
                                    <span></span>
                                    <span></span>
                                </div>
                            </div> : ''
                        )}
                    </div>
                </div>
            );
        });
    }

    render() {
        const voiceOptions = [
            { label: "Matthew (en-US)", value: "matthew" },
            { label: "Tiffany (en-US)", value: "tiffany" },
            { label: "Amy (en-GB)", value: "amy" }
        ];

        return (
            <div className="voice-agent">
                {this.state.alert && (
                    <Alert
                        type={this.state.alert.type || "error"}
                        dismissible={this.state.alert.dismissible !== false}
                        onDismiss={() => this.setState({alert: null})}
                        action={this.state.alert.showRestart ? (
                            <Button
                                variant="primary"
                                onClick={() => {
                                    this.setState({alert: null});
                                    // Auto-start conversation if not already started
                                    if (!this.state.sessionStarted) {
                                        this.handleSessionChange();
                                    }
                                }}
                            >
                                Restart Conversation
                            </Button>
                        ) : null}
                    >
                        {this.state.alert.message || this.state.alert}
                    </Alert>
                )}

                <Container>
                    <Header variant="h2">AWS Voice Assistant</Header>
                    
                    <SpaceBetween direction="vertical" size="l">
                        {/* Configuration Panel */}
                        <Container>
                            <Header variant="h3">Configuration</Header>
                            <ColumnLayout columns={3} variant="text-grid">
                                <FormField label="WebSocket URL">
                                    <input
                                        type="text"
                                        value={this.state.websocketUrl}
                                        onChange={(e) => this.setState({websocketUrl: e.target.value})}
                                        disabled={this.state.sessionStarted}
                                        style={{width: '100%', padding: '8px'}}
                                    />
                                </FormField>
                                
                                <FormField label="Voice">
                                    <Select
                                        selectedOption={this.state.configVoiceIdOption}
                                        onChange={({detail}) => this.setState({configVoiceIdOption: detail.selectedOption})}
                                        options={voiceOptions}
                                        disabled={this.state.sessionStarted}
                                    />
                                </FormField>

                                <div className="session-controls">
                                    <FormField label="Session Control">
                                        <Button
                                            variant={this.state.sessionStarted ? "normal" : "primary"}
                                            onClick={this.handleSessionChange}
                                        >
                                            {this.state.sessionStarted ? "End Conversation" : "Start Conversation"}
                                        </Button>
                                    </FormField>
                                    <div className="chat-history-option">
                                        <Checkbox
                                            checked={this.state.includeChatHistory}
                                            onChange={({detail}) => this.setState({includeChatHistory: detail.checked})}
                                            disabled={this.state.sessionStarted}
                                        >
                                            Include chat history
                                        </Checkbox>
                                        <div className="desc">Maintain conversation context across sessions</div>
                                    </div>
                                </div>
                            </ColumnLayout>
                        </Container>

                        {/* Main Content Area */}
                        <Grid gridDefinition={[{colspan: 6}, {colspan: 6}]}>
                            {/* Chat Area */}
                            <Container>
                                <Header variant="h3">Conversation</Header>
                                <div className="chat-area">
                                    {this.renderChatMessages()}
                                    <div ref={this.chatMessagesEndRef} className="end-marker" />
                                </div>
                            </Container>

                            {/* Events Area */}
                            <Container>
                                <Header variant="h3">Events</Header>
                                <div className="events-area">
                                    <EventDisplay ref={this.eventDisplayRef} />
                                </div>
                            </Container>
                        </Grid>
                    </SpaceBetween>
                </Container>
            </div>
        );
    }
}

export default VoiceAgent;
