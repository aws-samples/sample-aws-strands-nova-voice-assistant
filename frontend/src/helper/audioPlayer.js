export default class AudioPlayer {
    constructor() {
        this.initialized = false;
        this.audioContext = null;
        this.workletNode = null;
        this.analyser = null;
    }

    async start() {
        if (this.initialized) return;

        try {
            // Create audio context
            this.audioContext = new AudioContext({ "sampleRate": 24000 });
            
            // Resume audio context if suspended (required by browser autoplay policies)
            if (this.audioContext.state === 'suspended') {
                await this.audioContext.resume();
                console.log("Audio context resumed");
            }

            this.analyser = this.audioContext.createAnalyser();
            this.analyser.fftSize = 512;

            try {
                // Try to load the audio worklet
                const workletUrl = new URL('./audioPlayerProcessor.worklet.js', import.meta.url).toString();
                console.log("Loading audio worklet from:", workletUrl);
                
                await this.audioContext.audioWorklet.addModule(workletUrl);
                console.log("Audio worklet module loaded successfully");

                this.workletNode = new AudioWorkletNode(this.audioContext, "audio-player-processor");
                this.workletNode.connect(this.analyser);
                this.analyser.connect(this.audioContext.destination);
                
                console.log("AudioWorklet initialized successfully");
            } catch (workletError) {
                console.warn("AudioWorklet failed, falling back to basic audio:", workletError);
                
                // Create a simple gain node as fallback
                this.gainNode = this.audioContext.createGain();
                this.gainNode.connect(this.analyser);
                this.analyser.connect(this.audioContext.destination);
                
                console.log("Basic audio fallback initialized");
            }

            this.initialized = true;
            console.log("Audio player initialized successfully");
        } catch (error) {
            console.error("Failed to initialize audio player:", error);
            throw error;
        }
    }

    bargeIn() {
        if (!this.initialized) return;
        
        if (this.workletNode) {
            this.workletNode.port.postMessage({
                type: "barge-in",
            });
        } else {
            console.log("Barge-in called (fallback mode)");
            // In fallback mode, we don't have worklet messaging
        }
    }

    stop() {
        if (!this.initialized) return;

        if (this.audioContext) {
            this.audioContext.close();
        }

        if (this.analyser) {
            this.analyser.disconnect();
        }

        if (this.workletNode) {
            this.workletNode.disconnect();
        }

        this.initialized = false;
        this.audioContext = null;
        this.analyser = null;
        this.workletNode = null;
    }

    playAudio(samples) {
        if (!this.initialized) {
            console.error("The audio player is not initialized. Call start() before attempting to play audio.");
            return;
        }

        if (this.workletNode) {
            // Use AudioWorklet if available
            this.workletNode.port.postMessage({
                type: "audio",
                audioData: samples,
            });
        } else if (this.gainNode && samples) {
            // Fallback: Create audio buffer and play directly
            try {
                const audioBuffer = this.audioContext.createBuffer(1, samples.length, this.audioContext.sampleRate);
                const channelData = audioBuffer.getChannelData(0);
                
                // Copy samples to buffer
                for (let i = 0; i < samples.length; i++) {
                    channelData[i] = samples[i];
                }
                
                // Create buffer source and play
                const source = this.audioContext.createBufferSource();
                source.buffer = audioBuffer;
                source.connect(this.gainNode);
                source.start();
                
                console.log("Playing audio via fallback method");
            } catch (error) {
                console.error("Error playing audio via fallback:", error);
            }
        } else {
            console.warn("No audio playback method available");
        }
    }
}
