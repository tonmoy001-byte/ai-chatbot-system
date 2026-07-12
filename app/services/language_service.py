from typing import Optional, Dict, Any, List
import logging
import re

from app.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


# Supported languages
SUPPORTED_LANGUAGES = {
    "en": "English",
    "es": "Spanish",
    "fr": "French",
    "de": "German",
    "it": "Italian",
    "pt": "Portuguese",
    "nl": "Dutch",
    "ja": "Japanese",
    "ko": "Korean",
    "zh": "Chinese",
    "ar": "Arabic",
    "hi": "Hindi",
    "ru": "Russian"
}


class LanguageService:
    def __init__(self):
        self.supported_languages = SUPPORTED_LANGUAGES
        self.default_language = "en"
    
    async def detect_language(self, text: str) -> Dict[str, Any]:
        """
        Detect the language of input text.
        
        Args:
            text: Input text to analyze
        
        Returns:
            Dictionary with detected language info
        """
        if not text or len(text.strip()) == 0:
            return {
                "language": self.default_language,
                "confidence": 0.0,
                "supported": True
            }
        
        # Simple heuristic-based detection
        detected = self._simple_detect(text)
        
        return {
            "language": detected,
            "language_name": self.supported_languages.get(detected, "Unknown"),
            "confidence": 0.8,  # Placeholder confidence
            "supported": detected in self.supported_languages
        }
    
    def _simple_detect(self, text: str) -> str:
        """
        Simple language detection based on character patterns and common words.
        """
        text_lower = text.lower().strip()
        
        # Check for common patterns
        # Japanese (Hiragana, Katakana, Kanji)
        if re.search(r'[\u3040-\u309f\u30a0-\u30ff\u4e00-\u9faf]', text):
            return "ja"
        
        # Korean
        if re.search(r'[\uac00-\ud7af\u1100-\u11ff]', text):
            return "ko"
        
        # Chinese (simplified)
        if re.search(r'[\u4e00-\u9fff]', text):
            return "zh"
        
        # Arabic
        if re.search(r'[\u0600-\u06ff]', text):
            return "ar"
        
        # Hindi (Devanagari)
        if re.search(r'[\u0900-\u097f]', text):
            return "hi"
        
        # Russian (Cyrillic)
        if re.search(r'[\u0400-\u04ff]', text):
            return "ru"
        
        # Common word patterns for European languages
        common_words = {
            "en": ["the", "is", "are", "was", "were", "have", "has", "do", "does", "will", "can", "i", "you", "we", "they"],
            "es": ["el", "la", "los", "las", "es", "son", "está", "están", "tengo", "tienes", "tenemos", "yo", "tú", "nosotros"],
            "fr": ["le", "la", "les", "est", "sont", "ai", "as", "avons", "je", "tu", "nous", "vous", "ils", "elles"],
            "de": ["der", "die", "das", "ist", "sind", "haben", "ich", "du", "wir", "ihr", "sie", "ein", "eine"],
            "it": ["il", "la", "le", "è", "sono", "ho", "hai", "io", "tu", "noi", "voi", "loro", "un", "una"],
            "pt": ["o", "a", "os", "as", "é", "são", "tenho", "eu", "tu", "nós", "vocês", "eles", "elas"],
            "nl": ["de", "het", "een", "is", "zijn", "heb", "ik", "jij", "wij", "jullie", "zij"]
        }
        
        # Count matches for each language
        scores = {}
        for lang, words in common_words.items():
            score = sum(1 for word in words if word in text_lower.split())
            if score > 0:
                scores[lang] = score
        
        if scores:
            return max(scores, key=scores.get)
        
        return self.default_language
    
    async def translate_text(
        self,
        text: str,
        target_language: str,
        source_language: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Translate text to target language.
        
        Args:
            text: Text to translate
            target_language: Target language code
            source_language: Source language code (auto-detect if None)
        
        Returns:
            Dictionary with translation result
        """
        # Auto-detect if not provided
        if not source_language:
            detection = await self.detect_language(text)
            source_language = detection.get("language", self.default_language)
        
        # If same language, return original
        if source_language == target_language:
            return {
                "text": text,
                "source_language": source_language,
                "target_language": target_language,
                "translated": False
            }
        
        # In a real implementation, you would call a translation API
        # For now, return the original text with a note
        return {
            "text": text,
            "source_language": source_language,
            "target_language": target_language,
            "translated": False,
            "note": "Translation service not configured"
        }
    
    async def get_supported_languages(self) -> List[Dict[str, str]]:
        """Get list of supported languages."""
        return [
            {"code": code, "name": name}
            for code, name in self.supported_languages.items()
        ]
    
    def format_language_prompt(self, language_code: str) -> str:
        """
        Generate a system prompt for responding in a specific language.
        
        Args:
            language_code: Language code
        
        Returns:
            System prompt string
        """
        language_name = self.supported_languages.get(language_code, "English")
        
        return f"You are a multilingual customer service assistant. Please respond in {language_name}. If the customer writes in a different language, still respond in {language_name} unless they specifically request otherwise."
    
    async def format_multilingual_response(
        self,
        response_text: str,
        source_language: str,
        target_language: str
    ) -> Dict[str, Any]:
        """
        Format a response that may need translation.
        
        Args:
            response_text: The response text
            source_language: Language of the original message
            target_language: Desired response language
        
        Returns:
            Dictionary with formatted response
        """
        # If languages match, return as-is
        if source_language == target_language:
            return {
                "text": response_text,
                "translated": False,
                "language": target_language
            }
        
        # Try to translate
        translation = await self.translate_text(
            response_text,
            target_language,
            "en"  # Assume response is in English
        )
        
        return {
            "text": translation.get("text", response_text),
            "translated": translation.get("translated", False),
            "language": target_language,
            "original_language": source_language
        }
