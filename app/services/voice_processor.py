import httpx
from typing import Optional, Dict, Any, List
import tempfile
import os
import logging

from app.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


class VoiceProcessor:
    def __init__(self):
        self.api_key = settings.OPENAI_API_KEY
        self.whisper_api = "https://api.openai.com/v1/audio/transcriptions"
        self.translate_api = "https://api.openai.com/v1/audio/translations"
    
    async def transcribe(
        self,
        audio_url: str,
        language: Optional[str] = None,
        response_format: str = "text"
    ) -> Optional[Dict[str, Any]]:
        """
        Transcribe voice message using Whisper API.
        
        Args:
            audio_url: URL of the audio file
            language: Optional language code (e.g., 'en', 'es')
            response_format: Output format ('text', 'json', 'verbose_json')
        
        Returns:
            Dictionary with transcription result
        """
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                # Download audio file
                audio_response = await client.get(audio_url)
                audio_response.raise_for_status()
                
                # Determine file extension from content type
                content_type = audio_response.headers.get("content-type", "audio/ogg")
                ext = self._get_extension_from_content_type(content_type)
                
                # Save to temporary file
                with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
                    tmp.write(audio_response.content)
                    tmp_path = tmp.name
                
                try:
                    # Prepare form data
                    form_data = {
                        "model": "whisper-1",
                        "response_format": response_format
                    }
                    if language:
                        form_data["language"] = language
                    
                    # Transcribe
                    with open(tmp_path, "rb") as audio_file:
                        response = await client.post(
                            self.whisper_api,
                            headers={"Authorization": f"Bearer {self.api_key}"},
                            files={"file": (f"audio{ext}", audio_file, content_type)},
                            data=form_data
                        )
                        response.raise_for_status()
                        
                        result = response.json()
                        
                        # Format response
                        if response_format == "text":
                            return {
                                "text": result if isinstance(result, str) else result.get("text", ""),
                                "language": language or "unknown",
                                "success": True
                            }
                        else:
                            return {
                                "text": result.get("text", ""),
                                "language": result.get("language", language or "unknown"),
                                "duration": result.get("duration", 0),
                                "segments": result.get("segments", []),
                                "success": True
                            }
                
                finally:
                    # Clean up temporary file
                    os.unlink(tmp_path)
        
        except httpx.HTTPStatusError as e:
            logger.error(f"Whisper API error: {e.response.status_code} - {e.response.text}")
            return {"text": "", "success": False, "error": f"API error: {e.response.status_code}"}
        except Exception as e:
            logger.error(f"Transcription failed: {str(e)}")
            return {"text": "", "success": False, "error": str(e)}
    
    async def translate(
        self,
        audio_url: str,
        target_language: str = "en"
    ) -> Optional[Dict[str, Any]]:
        """
        Translate audio to target language using Whisper API.
        
        Args:
            audio_url: URL of the audio file
            target_language: Target language code
        
        Returns:
            Dictionary with translation result
        """
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                # Download audio file
                audio_response = await client.get(audio_url)
                audio_response.raise_for_status()
                
                content_type = audio_response.headers.get("content-type", "audio/ogg")
                ext = self._get_extension_from_content_type(content_type)
                
                with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
                    tmp.write(audio_response.content)
                    tmp_path = tmp.name
                
                try:
                    with open(tmp_path, "rb") as audio_file:
                        response = await client.post(
                            self.translate_api,
                            headers={"Authorization": f"Bearer {self.api_key}"},
                            files={"file": (f"audio{ext}", audio_file, content_type)},
                            data={"model": "whisper-1"}
                        )
                        response.raise_for_status()
                        
                        result = response.json()
                        
                        return {
                            "text": result.get("text", ""),
                            "original_language": "unknown",
                            "target_language": target_language,
                            "success": True
                        }
                
                finally:
                    os.unlink(tmp_path)
        
        except Exception as e:
            logger.error(f"Translation failed: {str(e)}")
            return {"text": "", "success": False, "error": str(e)}
    
    async def detect_language(self, audio_url: str) -> Optional[str]:
        """
        Detect language of voice message.
        
        Args:
            audio_url: URL of the audio file
        
        Returns:
            Language code or None if detection fails
        """
        result = await self.transcribe(audio_url, response_format="verbose_json")
        if result and result.get("success"):
            return result.get("language")
        return None
    
    async def transcribe_with_segments(
        self,
        audio_url: str,
        language: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Transcribe audio with detailed segment information.
        
        Returns:
            Dictionary with full transcription details including timestamps
        """
        return await self.transcribe(audio_url, language, response_format="verbose_json")
    
    async def process_voice_message(
        self,
        audio_url: str,
        auto_translate: bool = False,
        target_language: str = "en"
    ) -> Dict[str, Any]:
        """
        Process a voice message with full pipeline.
        
        Args:
            audio_url: URL of the audio file
            auto_translate: Whether to translate non-English audio
            target_language: Target language for translation
        
        Returns:
            Complete processing result
        """
        # First, detect language and transcribe
        transcription = await self.transcribe_with_segments(audio_url)
        
        if not transcription or not transcription.get("success"):
            return {
                "success": False,
                "error": transcription.get("error", "Transcription failed"),
                "text": ""
            }
        
        detected_language = transcription.get("language", "unknown")
        text = transcription.get("text", "")
        
        # Translate if needed
        translation = None
        if auto_translate and detected_language != target_language:
            translation = await self.translate(audio_url, target_language)
        
        return {
            "success": True,
            "text": text,
            "detected_language": detected_language,
            "duration": transcription.get("duration", 0),
            "segments": transcription.get("segments", []),
            "translation": translation.get("text") if translation else None,
            "translated_language": target_language if translation else None
        }
    
    def _get_extension_from_content_type(self, content_type: str) -> str:
        """Get file extension from content type."""
        content_type_map = {
            "audio/ogg": ".ogg",
            "audio/mpeg": ".mp3",
            "audio/mp4": ".m4a",
            "audio/wav": ".wav",
            "audio/x-wav": ".wav",
            "audio/webm": ".webm"
        }
        
        for ct, ext in content_type_map.items():
            if ct in content_type.lower():
                return ext
        
        return ".ogg"  # Default
