"""
Event definitions for Amazon Nova Sonic integration.
Based on the s2s_events.py from Amazon Nova samples.
"""

import json


class S2sEvent:
    """
    Utility class for creating events for Amazon Nova Sonic.
    """

    # Default configuration values
    DEFAULT_INFER_CONFIG = {
        "maxTokens": 1024,
        "topP": 1.0,  # Using 1.0 for better tool calling reliability
        "temperature": 1.0,  # Using 1.0 for better tool calling reliability
        "topK": 1,  # Using 1 for better tool calling reliability
    }

    DEFAULT_SYSTEM_PROMPT = """You are a specialized AWS assistant that ONLY helps with AWS services and operations.
    
    IMPORTANT: You ONLY handle AWS-related queries. If users ask about non-AWS topics, politely respond: "I'm specialized in AWS services only. Please ask about EC2, SSM, Backup, or other AWS services."
    
    When you need to get information about AWS services or perform operations, use the supervisorAgent tool.
    The supervisorAgent will route your query to specialized agents for EC2, Backup, and SSM.
    Always use the supervisorAgent tool when the user asks about AWS services or operations.
    
    Keep responses concise and focused on AWS services only."""

    DEFAULT_AUDIO_INPUT_CONFIG = {
        "mediaType": "audio/lpcm",
        "sampleRateHertz": 16000,
        "sampleSizeBits": 16,
        "channelCount": 1,
        "audioType": "SPEECH",
        "encoding": "base64",
    }

    DEFAULT_AUDIO_OUTPUT_CONFIG = {
        "mediaType": "audio/lpcm",
        "sampleRateHertz": 24000,
        "sampleSizeBits": 16,
        "channelCount": 1,
        "voiceId": "matthew",
        "encoding": "base64",
        "audioType": "SPEECH",
    }

    # Tool configuration for the Supervisor Agent
    SUPERVISOR_TOOL_CONFIG = {
        "tools": [
            {
                "toolSpec": {
                    "name": "supervisorAgent",
                    "description": "Routes queries to specialized agents for EC2, Backup, and SSM",
                    "inputSchema": {
                        "json": """{
                            "$schema": "http://json-schema.org/draft-07/schema#",
                            "type": "object",
                            "properties": {
                                "query": {
                                    "type": "string",
                                    "description": "The user query about AWS services or operations"
                                }
                            },
                            "required": ["query"]
                        }"""
                    },
                }
            }
        ]
    }

    @staticmethod
    def session_start(inference_config=DEFAULT_INFER_CONFIG):
        """Create a session start event."""
        return {"event": {"sessionStart": {"inferenceConfiguration": inference_config}}}

    @staticmethod
    def prompt_start(
        prompt_name,
        audio_output_config=DEFAULT_AUDIO_OUTPUT_CONFIG,
        tool_config=SUPERVISOR_TOOL_CONFIG,
    ):
        """Create a prompt start event."""
        return {
            "event": {
                "promptStart": {
                    "promptName": prompt_name,
                    "textOutputConfiguration": {"mediaType": "text/plain"},
                    "audioOutputConfiguration": audio_output_config,
                    "toolUseOutputConfiguration": {"mediaType": "application/json"},
                    "toolConfiguration": tool_config,
                }
            }
        }

    @staticmethod
    def content_start_text(prompt_name, content_name):
        """Create a content start event for text."""
        return {
            "event": {
                "contentStart": {
                    "promptName": prompt_name,
                    "contentName": content_name,
                    "type": "TEXT",
                    "interactive": True,
                    "role": "SYSTEM",
                    "textInputConfiguration": {"mediaType": "text/plain"},
                }
            }
        }

    @staticmethod
    def text_input(prompt_name, content_name, system_prompt=DEFAULT_SYSTEM_PROMPT):
        """Create a text input event."""
        return {
            "event": {
                "textInput": {
                    "promptName": prompt_name,
                    "contentName": content_name,
                    "content": system_prompt,
                }
            }
        }

    @staticmethod
    def content_end(prompt_name, content_name):
        """Create a content end event."""
        return {
            "event": {
                "contentEnd": {"promptName": prompt_name, "contentName": content_name}
            }
        }

    @staticmethod
    def content_start_audio(
        prompt_name, content_name, audio_input_config=DEFAULT_AUDIO_INPUT_CONFIG
    ):
        """Create a content start event for audio."""
        return {
            "event": {
                "contentStart": {
                    "promptName": prompt_name,
                    "contentName": content_name,
                    "type": "AUDIO",
                    "interactive": True,
                    "audioInputConfiguration": audio_input_config,
                }
            }
        }

    @staticmethod
    def audio_input(prompt_name, content_name, content):
        """Create an audio input event."""
        return {
            "event": {
                "audioInput": {
                    "promptName": prompt_name,
                    "contentName": content_name,
                    "content": content,
                }
            }
        }

    @staticmethod
    def content_start_tool(prompt_name, content_name, tool_use_id):
        """Create a content start event for a tool."""
        return {
            "event": {
                "contentStart": {
                    "promptName": prompt_name,
                    "contentName": content_name,
                    "interactive": True,
                    "type": "TOOL",
                    "role": "TOOL",
                    "toolResultInputConfiguration": {
                        "toolUseId": tool_use_id,
                        "type": "TEXT",
                        "textInputConfiguration": {"mediaType": "text/plain"},
                    },
                }
            }
        }

    @staticmethod
    def text_input_tool(prompt_name, content_name, content):
        """Create a text input event for a tool result."""
        return {
            "event": {
                "toolResult": {
                    "promptName": prompt_name,
                    "contentName": content_name,
                    "content": content,
                }
            }
        }

    @staticmethod
    def prompt_end(prompt_name):
        """Create a prompt end event."""
        return {"event": {"promptEnd": {"promptName": prompt_name}}}

    @staticmethod
    def session_end():
        """Create a session end event."""
        return {"event": {"sessionEnd": {}}}
