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
    SENSITIVITY_ACTIONS = {
        'low': ('mute', 5),          # least restrictive
        'medium': ('fast_forward', 10),
        'high': ('skip', 15)         # most restrictive
    }
    SEXUAL_KEYWORDS = ['sex', 'sexual', 'naked', 'nude', 'explicit', 'rape', 'intercourse', 'seduce', 'seduction']
    VIOLENCE_KEYWORDS = ['kill', 'killed', 'murder', 'shot', 'shoot', 'stab', 'blood', 'violence', 'violent', 'attack', 'fight', 'gun', 'weapon', 'death', 'die', 'dying', 'dead', 'assault', 'beat', 'beating', 'punch', 'hit']
    
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
        severity = self._count_whole_words(text, self.SEXUAL_KEYWORDS)
        for pattern in self.SEXUAL_PATTERNS:
            matches = re.findall(pattern, text, re.IGNORECASE)
            severity += len(matches)
        return severity
    
    def _check_violence(self, text: str) -> int:
        """Check for violent content and return severity score."""
        severity = self._count_whole_words(text, self.VIOLENCE_KEYWORDS)
        for pattern in self.VIOLENCE_PATTERNS:
            matches = re.findall(pattern, text, re.IGNORECASE)
            severity += len(matches)
        return severity

    def _count_whole_words(self, text: str, words: List[str]) -> int:
        """Count whole-word occurrences for simple keyword lists."""
        count = 0
        for word in words:
            count += len(re.findall(rf'\b{re.escape(word)}\b', text, re.IGNORECASE))
        return count

    def analyze_decision(self, text: str, preferences: Dict, confidence: float | None = None) -> Dict:
        """
        Return structured decision with priority: sexual > violence > language.
        Sensitivity deterministically maps to action+duration.
        """

        def base_decision(reason: str) -> Dict:
            return {
                "action": "none",
                "duration_seconds": 0,
                "matched_category": None,
                "reason": reason
            }

        if not text:
            return base_decision("No match")

        text_lower = text.lower()
        severities = {
            'language': self._check_language(text_lower) if preferences.get('language_filter', True) else 0,
            'sexual': self._check_sexual_content(text_lower) if preferences.get('sexual_content_filter', True) else 0,
            'violence': self._check_violence(text_lower) if preferences.get('violence_filter', True) else 0
        }

        def passed(category: str) -> bool:
            sensitivity_key = f"{category}_sensitivity"
            threshold = self.SENSITIVITY_THRESHOLDS.get(preferences.get(sensitivity_key, 'medium'), 2)
            return severities[category] >= threshold

        for category in ['sexual', 'violence', 'language']:
            if not passed(category):
                continue
            sensitivity_key = f"{category}_sensitivity"
            sensitivity = preferences.get(sensitivity_key, 'medium')
            action, duration = self.SENSITIVITY_ACTIONS.get(sensitivity, self.SENSITIVITY_ACTIONS['medium'])
            reason_parts = [
                f"{category} content detected",
                f"sensitivity={sensitivity}",
                f"severity={severities[category]}"
            ]
            if confidence is not None:
                reason_parts.append(f"confidence={confidence}")
            return {
                "action": action,
                "duration_seconds": duration,
                "matched_category": category,
                "reason": "; ".join(reason_parts)
            }

        return base_decision("No match")
