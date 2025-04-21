"""OpenAI TTS provider implementation."""

import openai
from typing import List, Optional, Tuple
from ..base import TTSProvider

class OpenAITTS(TTSProvider):
    """OpenAI Text-to-Speech provider."""
    
    # Provider-specific SSML tags
    PROVIDER_SSML_TAGS: List[str] = ['break', 'emphasis']
    
    def __init__(self, api_key: Optional[str] = None, model: str = "tts-1-hd"):
        """
        Initialize OpenAI TTS provider.
        
        Args:
            api_key: OpenAI API key. If None, expects OPENAI_API_KEY env variable
            model: Model name to use. Defaults to "tts-1-hd"
        """
        if api_key:
            openai.api_key = api_key
        elif not openai.api_key:
            raise ValueError("OpenAI API key must be provided or set in environment")
        self.model = model
            
    def get_supported_tags(self) -> List[str]:
        """Get all supported SSML tags including provider-specific ones."""
        return self.PROVIDER_SSML_TAGS
        
    def generate_audio(self, text: str, voice: str, model: str, voice2: str = None) -> bytes:
        """Generate audio using OpenAI API."""
        self.validate_parameters(text, voice, model)
        
        try:
            response = openai.audio.speech.create(
                model=model,
                voice=voice,
                input=text
            )
            return response.content
        except Exception as e:
            raise RuntimeError(f"Failed to generate audio: {str(e)}") from e

    def split_qa(self, input_text: str, ending_message: str, supported_tags: List[str] = None) -> List[Tuple[str, str]]:
        """
        Split the input text into question-answer pairs.
        For OpenAI TTS, we'll format the text as a conversation between two speakers.
        """
        # Format the text as a conversation
        lines = input_text.split('\n')
        formatted_text = []
        is_person1 = True
        
        for line in lines:
            line = line.strip()
            if line:
                if is_person1:
                    formatted_text.append(f"<Person1>{line}</Person1>")
                else:
                    formatted_text.append(f"<Person2>{line}</Person2>")
                is_person1 = not is_person1
        
        # Add ending message
        if ending_message:
            formatted_text.append(f"<Person2>{ending_message}</Person2>")
        
        # Join the formatted text
        formatted_input = "\n".join(formatted_text)
        
        # Use the parent class's split_qa method
        return super().split_qa(formatted_input, "", supported_tags)