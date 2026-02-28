/**
 * Helper for creating BidiAgent-compatible WebSocket messages.
 * Replaces the S2sEvent class for the single-hop BidiAgent architecture.
 */
export const BidiEventHelpers = {
  audioInput(base64Data) {
    return { type: "bidi_audio_input", data: base64Data };
  },
  textInput(text) {
    return { type: "bidi_text_input", text };
  },
  config(voiceId, sessionId) {
    const msg = { type: "config", voice_id: voiceId };
    if (sessionId) msg.session_id = sessionId;
    return msg;
  },
  close() {
    return { type: "close" };
  },
};
