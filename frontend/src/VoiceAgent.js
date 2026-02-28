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
    Grid
} from '@cloudscape-design/components';
import { BidiEventHelpers } from './helper/BidiEventHelpers';
import EventDisplay from './components/EventDisplay';
import { base64ToFloat32Array } from './helper/audioHelper';
import AudioPlayer from './helper/audioPlayer';

class VoiceAgent extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            status: "loading",
            alert: null,
            sessionStarted: false,
            showEventJson: false,
            showConfig: false,
            selectedEvent: null,

            chatMessages: {},
            events: [],
            audioChunks: [],
            audioPlayPromise: null,
            messageCounter: 0,
            currentTranscriptKey: null,

            configVoiceIdOption: { label: "Matthew (en-US)", value: "matthew" },
            websocketUrl: "ws://localhost:8080",
            sessionId: crypto.randomUUID(),
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
        var chatMessages = this.state.chatMessages;

        switch (message.type) {
            case "bidi_audio_stream":
                try {
                    const base64Data = message.data;

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
                        this.audioBufferSize = chunkSize;
                    }

                    const audioData = base64ToFloat32Array(base64Data);
                    this.audioPlayer.playAudio(audioData);
                } catch (error) {
                    console.error("Error processing audio chunk:", error);
                }
                break;

            case "bidi_transcript_stream": {
                const role = message.role;
                const text = message.text;
                const isFinal = message.is_final;

                if (!role || text === undefined) break;

                if (isFinal) {
                    // Final transcript — create a new finalized message entry
                    const counter = this.state.messageCounter + 1;
                    const key = `${role}-${counter}`;
                    chatMessages[key] = {
                        content: text,
                        role: role,
                    };
                    this.setState({ chatMessages: chatMessages, messageCounter: counter, currentTranscriptKey: null });
                } else {
                    // Interim transcript — update in-progress message
                    const currentKey = this.state.currentTranscriptKey;
                    const key = currentKey && chatMessages[currentKey]?.role === role
                        ? currentKey
                        : `${role}-interim`;

                    chatMessages[key] = {
                        content: text,
                        role: role,
                    };
                    this.setState({ chatMessages: chatMessages, currentTranscriptKey: key });
                }
                break;
            }

            case "bidi_interruption":
                this.cancelAudio();
                break;

            case "bidi_connection_start":
                console.log("BidiAgent connection started", message.connection_id);
                break;

            case "bidi_connection_close":
                console.log("BidiAgent connection closed", message.reason);
                this.setState({
                    alert: {
                        type: "warning",
                        message: message.reason || "Connection closed. Please restart your conversation.",
                        dismissible: true,
                        showRestart: true
                    }
                });
                if (this.state.sessionStarted) {
                    this.endSession();
                    this.setState({ sessionStarted: false });
                }
                break;

            case "bidi_connection_restart":
                console.log("BidiAgent connection restarting");
                break;

            case "bidi_response_start":
                // Optionally show loading indicator
                break;

            case "bidi_response_complete":
                // Clear loading indicator
                break;

            case "bidi_error":
                this.setState({
                    alert: {
                        type: "error",
                        message: message.message || "An error occurred.",
                        dismissible: true,
                        showRestart: true
                    }
                });
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
                messageCounter: 0,
                currentTranscriptKey: null,
            });
            if (this.eventDisplayRef.current) this.eventDisplayRef.current.cleanup();
            
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
        if (this.socket === null || this.socket.readyState !== WebSocket.OPEN) {
            this.socket = new WebSocket(this.state.websocketUrl);
            
            this.socket.onopen = () => {
                console.log("WebSocket connected!");
                this.setState({status: "connected"});

                // Send config message with selected voice
                this.sendEvent(BidiEventHelpers.config(this.state.configVoiceIdOption.value, this.state.sessionId));
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
                
                if (this.state.sessionStarted) {
                    this.endSession();
                    this.setState({ sessionStarted: false });
                }
            };

            // Handle connection close
            this.socket.onclose = (event) => {
                console.log("WebSocket Disconnected", event.code, event.reason);
                this.setState({status: "disconnected"});
                
                if (event.code === 1005) {
                    this.setState({
                        alert: {
                            type: "warning",
                            message: "Connection lost unexpectedly. Please restart your conversation.",
                            dismissible: true,
                            showRestart: true
                        }
                    });
                } else if (event.code !== 1000) {
                    this.setState({
                        alert: {
                            type: "error",
                            message: `Connection closed unexpectedly (${event.code}). Please restart your conversation.`,
                            dismissible: true,
                            showRestart: true
                        }
                    });
                }
                
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

                    // Send audio data using BidiEventHelpers
                    this.sendEvent(BidiEventHelpers.audioInput(base64Data));
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

        // Send close event and close WebSocket
        if (this.socket && this.socket.readyState === WebSocket.OPEN) {
            try {
                this.sendEvent(BidiEventHelpers.close());
            } catch (error) {
                console.warn("Error sending close event:", error);
            }
            
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
        });
        
        console.log('Session ended and cleaned up');
    }

    renderChatMessages() {
        const messages = Object.entries(this.state.chatMessages)
            .map(([key, msg]) => ({ key, ...msg }))
            .sort((a, b) => {
                // Sort by key to maintain insertion order
                const aNum = parseInt(a.key.split('-').pop()) || 0;
                const bNum = parseInt(b.key.split('-').pop()) || 0;
                return aNum - bNum;
            });

        return messages.map((message) => {
            const isUser = message.role === "user";
            const isAssistant = message.role === "assistant";
            
            if (!isUser && !isAssistant) return null;

            return (
                <div key={message.key} className={`chat-item ${isUser ? 'user' : 'bot'}`}>
                    <div className={`message-bubble ${isUser ? 'user-message' : 'bot-message'}`}>
                        {message.content || ''}
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
                                        <SpaceBetween direction="horizontal" size="xs">
                                            <Button
                                                variant={this.state.sessionStarted ? "normal" : "primary"}
                                                onClick={this.handleSessionChange}
                                            >
                                                {this.state.sessionStarted ? "End Conversation" : "Start Conversation"}
                                            </Button>
                                            <Button
                                                variant="normal"
                                                onClick={() => {
                                                    if (this.state.sessionStarted) {
                                                        this.endSession();
                                                        this.cancelAudio();
                                                        this.audioPlayer.start();
                                                    }
                                                    this.setState({
                                                        sessionId: crypto.randomUUID(),
                                                        chatMessages: {},
                                                        messageCounter: 0,
                                                        currentTranscriptKey: null,
                                                        sessionStarted: false,
                                                    });
                                                    if (this.eventDisplayRef.current) this.eventDisplayRef.current.cleanup();
                                                }}
                                            >
                                                New Session
                                            </Button>
                                        </SpaceBetween>
                                    </FormField>
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
