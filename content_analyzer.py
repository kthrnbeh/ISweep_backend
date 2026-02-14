import re
from typing import Dict, List, Tuple
from better_profanity import profanity

class ContentAnalyzer:
    """Analyzes caption/transcript text and determines playback control actions."""
    
    # Define content patterns for different categories
    VIOLENCE_PATTERNS = [
        r'\b(kill|killed|murder|shot|shoot|stab|blood|violence|violent|attack|fight|gun|weapon)\b',
        r'\b(death|die|dying|dead)\b',
        r'\b(assault|beat|beating|punch|hit)\b'
    ]
    
    SEXUAL_PATTERNS = [
        r'\b(sex|sexual|naked|nude|explicit)\b',
        r'\b(rape|assault|abuse)\b',
        r'\b(intercourse|seduce|seduction)\b'
    ]
    
    # Sensitivity thresholds (number of matches before triggering action)
    SENSITIVITY_THRESHOLDS = {
        'low': 5,      # Very lenient, needs many matches
        'medium': 2,   # Moderate sensitivity
        'high': 1      # Very strict, one match triggers action
    }
    
    def __init__(self):
        """Initialize the content analyzer."""
        profanity.load_censor_words()
    
    def analyze(self, text: str, user_preferences: Dict) -> str:
        """
        Analyze text and return playback action based on user preferences.
        
        Args:
            text: Caption or transcript text to analyze
            user_preferences: User's filtering preferences
            
        Returns:
            One of: 'mute', 'skip', 'fast_forward', 'none'
        """
        if not text:
            return 'none'
        
        text_lower = text.lower()
        
        # Check language (profanity) filter
        if user_preferences.get('language_filter', True):
            language_severity = self._check_language(text_lower)
            threshold = self.SENSITIVITY_THRESHOLDS.get(
                user_preferences.get('language_sensitivity', 'medium'), 2
            )
            if language_severity >= threshold:
                return 'mute'  # Mute for brief profanity
        
        # Check sexual content filter
        if user_preferences.get('sexual_content_filter', True):
            sexual_severity = self._check_sexual_content(text_lower)
            threshold = self.SENSITIVITY_THRESHOLDS.get(
                user_preferences.get('sexual_content_sensitivity', 'medium'), 2
            )
            if sexual_severity >= threshold:
                return 'skip'  # Skip sexual content scenes
        
        # Check violence filter
        if user_preferences.get('violence_filter', True):
            violence_severity = self._check_violence(text_lower)
            threshold = self.SENSITIVITY_THRESHOLDS.get(
                user_preferences.get('violence_sensitivity', 'medium'), 2
            )
            if violence_severity >= threshold:
                return 'fast_forward'  # Fast forward through violence
        
        return 'none'
    
    def _check_language(self, text: str) -> int:
        """Check for profanity in text and return severity score."""
        # Use better-profanity library to detect profanity
        if profanity.contains_profanity(text):
            # Count profane words
            words = text.split()
            profane_count = sum(1 for word in words if profanity.contains_profanity(word))
            return profane_count
        return 0
    
    def _check_sexual_content(self, text: str) -> int:
        """Check for sexual content and return severity score."""
        severity = 0
        for pattern in self.SEXUAL_PATTERNS:
            matches = re.findall(pattern, text, re.IGNORECASE)
            severity += len(matches)
        return severity
    
    def _check_violence(self, text: str) -> int:
        """Check for violent content and return severity score."""
        severity = 0
        for pattern in self.VIOLENCE_PATTERNS:
            matches = re.findall(pattern, text, re.IGNORECASE)
            severity += len(matches)
        return severity
