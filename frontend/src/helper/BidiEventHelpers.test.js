import { BidiEventHelpers } from "./BidiEventHelpers";

describe("BidiEventHelpers", () => {
  test("audioInput returns correct structure with base64 data", () => {
    const result = BidiEventHelpers.audioInput("dGVzdA==");
    expect(result).toEqual({ type: "bidi_audio_input", data: "dGVzdA==" });
  });

  test("textInput returns correct structure with text", () => {
    const result = BidiEventHelpers.textInput("hello world");
    expect(result).toEqual({ type: "bidi_text_input", text: "hello world" });
  });

  test("config returns correct structure with voice ID", () => {
    const result = BidiEventHelpers.config("tiffany");
    expect(result).toEqual({ type: "config", voice_id: "tiffany" });
  });

  test("close returns correct structure", () => {
    const result = BidiEventHelpers.close();
    expect(result).toEqual({ type: "close" });
  });
});
