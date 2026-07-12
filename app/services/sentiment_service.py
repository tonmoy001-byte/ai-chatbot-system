from typing import Dict, Any, Optional, List
from enum import Enum
import logging
import re

from app.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


class SentimentLevel(str, Enum):
    VERY_POSITIVE = "very_positive"
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"
    VERY_NEGATIVE = "very_negative"


class UrgencyLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# Sentiment keywords
POSITIVE_WORDS = [
    "good", "great", "excellent", "amazing", "wonderful", "fantastic",
    "love", "like", "happy", "pleased", "thank", "thanks", "perfect",
    "awesome", "best", "helpful", "friendly", "quick", "fast", "easy"
]

NEGATIVE_WORDS = [
    "bad", "terrible", "awful", "horrible", "hate", "angry", "mad",
    "frustrated", "annoyed", "disappointed", "unhappy", "poor", "worst",
    "slow", "difficult", "complicated", "confusing", "broken", "wrong"
]

URGENCY_WORDS = [
    "urgent", "asap", "immediately", "emergency", "critical", "now",
    "hurry", "fast", "quickly", "help", "stuck", "problem", "issue"
]

COMPLAINT_WORDS = [
    "complaint", "refund", "cancel", "return", "exchange", "damaged",
    "defective", "wrong", "missing", "lost", "never received", "not working"
]


class SentimentAnalyzer:
    def __init__(self):
        self.positive_words = set(POSITIVE_WORDS)
        self.negative_words = set(NEGATIVE_WORDS)
        self.urgency_words = set(URGENCY_WORDS)
        self.complaint_words = set(COMPLAINT_WORDS)
    
    async def analyze(self, text: str) -> Dict[str, Any]:
        """
        Analyze sentiment of input text.
        
        Args:
            text: Input text to analyze
        
        Returns:
            Dictionary with sentiment analysis results
        """
        if not text or len(text.strip()) == 0:
            return self._default_result()
        
        text_lower = text.lower().strip()
        words = re.findall(r'\b\w+\b', text_lower)
        
        # Calculate scores
        positive_score = sum(1 for w in words if w in self.positive_words)
        negative_score = sum(1 for w in words if w in self.negative_words)
        urgency_score = sum(1 for w in words if w in self.urgency_words)
        complaint_score = sum(1 for w in words if w in self.complaint_words)
        
        # Check for negation
        negation_words = ["not", "no", "never", "neither", "nobody", "nothing"]
        has_negation = any(w in negation_words for w in words)
        
        # Adjust scores for negation
        if has_negation:
            positive_score, negative_score = negative_score, positive_score
        
        # Calculate overall sentiment score (-1 to 1)
        total_words = len(words) if words else 1
        sentiment_score = (positive_score - negative_score) / max(total_words, 1)
        
        # Determine sentiment level
        sentiment_level = self._get_sentiment_level(sentiment_score)
        
        # Determine urgency
        urgency_level = self._get_urgency_level(urgency_score, text_lower)
        
        # Check for complaint indicators
        is_complaint = complaint_score > 0
        
        return {
            "sentiment_score": round(sentiment_score, 3),
            "sentiment_level": sentiment_level.value,
            "urgency_level": urgency_level.value,
            "is_complaint": is_complaint,
            "has_negation": has_negation,
            "positive_words_found": [w for w in words if w in self.positive_words],
            "negative_words_found": [w for w in words if w in self.negative_words],
            "urgency_words_found": [w for w in words if w in self.urgency_words],
            "complaint_words_found": [w for w in words if w in self.complaint_words],
            "should_escalate": self._should_escalate(sentiment_level, urgency_level, is_complaint)
        }
    
    async def analyze_conversation(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        Analyze sentiment across multiple messages.
        
        Args:
            messages: List of messages with 'role' and 'content'
        
        Returns:
            Dictionary with conversation-level sentiment analysis
        """
        if not messages:
            return {
                "overall_sentiment": SentimentLevel.NEUTRAL.value,
                "average_score": 0.0,
                "trend": "stable",
                "escalation_recommended": False
            }
        
        # Analyze each customer message
        customer_messages = [m for m in messages if m.get("role") == "user"]
        
        if not customer_messages:
            return {
                "overall_sentiment": SentimentLevel.NEUTRAL.value,
                "average_score": 0.0,
                "trend": "stable",
                "escalation_recommended": False
            }
        
        # Get sentiment for each message
        sentiments = []
        for msg in customer_messages:
            result = await self.analyze(msg.get("content", ""))
            sentiments.append(result["sentiment_score"])
        
        # Calculate average
        average_score = sum(sentiments) / len(sentiments) if sentiments else 0
        
        # Determine trend (improving, declining, stable)
        trend = self._calculate_trend(sentiments)
        
        # Overall sentiment
        overall_sentiment = self._get_sentiment_level(average_score)
        
        # Check if escalation is recommended
        escalation_recommended = (
            average_score < -0.3 or
            any(s < -0.5 for s in sentiments) or
            trend == "declining"
        )
        
        return {
            "overall_sentiment": overall_sentiment.value,
            "average_score": round(average_score, 3),
            "message_scores": sentiments,
            "trend": trend,
            "escalation_recommended": escalation_recommended,
            "message_count": len(customer_messages)
        }
    
    def _get_sentiment_level(self, score: float) -> SentimentLevel:
        """Convert score to sentiment level."""
        if score > 0.3:
            return SentimentLevel.VERY_POSITIVE
        elif score > 0.1:
            return SentimentLevel.POSITIVE
        elif score > -0.1:
            return SentimentLevel.NEUTRAL
        elif score > -0.3:
            return SentimentLevel.NEGATIVE
        else:
            return SentimentLevel.VERY_NEGATIVE
    
    def _get_urgency_level(self, urgency_score: int, text: str) -> UrgencyLevel:
        """Determine urgency level."""
        # Check for critical keywords
        critical_patterns = ["emergency", "urgent", "asap", "immediately"]
        if any(p in text for p in critical_patterns):
            return UrgencyLevel.CRITICAL
        
        if urgency_score >= 3:
            return UrgencyLevel.HIGH
        elif urgency_score >= 2:
            return UrgencyLevel.MEDIUM
        elif urgency_score >= 1:
            return UrgencyLevel.LOW
        
        # Check for exclamation marks
        if text.count("!") >= 3:
            return UrgencyLevel.MEDIUM
        
        return UrgencyLevel.LOW
    
    def _should_escalate(
        self,
        sentiment: SentimentLevel,
        urgency: UrgencyLevel,
        is_complaint: bool
    ) -> bool:
        """Determine if message should be escalated to human agent."""
        # Escalate for very negative sentiment
        if sentiment == SentimentLevel.VERY_NEGATIVE:
            return True
        
        # Escalate for critical urgency
        if urgency == UrgencyLevel.CRITICAL:
            return True
        
        # Escalate for complaints
        if is_complaint:
            return True
        
        # Escalate for negative sentiment with high urgency
        if sentiment == SentimentLevel.NEGATIVE and urgency == UrgencyLevel.HIGH:
            return True
        
        return False
    
    def _calculate_trend(self, scores: List[float]) -> str:
        """Calculate sentiment trend from list of scores."""
        if len(scores) < 2:
            return "stable"
        
        # Compare first half average to second half average
        mid = len(scores) // 2
        first_half_avg = sum(scores[:mid]) / mid if mid > 0 else 0
        second_half_avg = sum(scores[mid:]) / (len(scores) - mid) if (len(scores) - mid) > 0 else 0
        
        diff = second_half_avg - first_half_avg
        
        if diff > 0.1:
            return "improving"
        elif diff < -0.1:
            return "declining"
        else:
            return "stable"
    
    def _default_result(self) -> Dict[str, Any]:
        """Return default analysis result."""
        return {
            "sentiment_score": 0.0,
            "sentiment_level": SentimentLevel.NEUTRAL.value,
            "urgency_level": UrgencyLevel.LOW.value,
            "is_complaint": False,
            "has_negation": False,
            "positive_words_found": [],
            "negative_words_found": [],
            "urgency_words_found": [],
            "complaint_words_found": [],
            "should_escalate": False
        }
