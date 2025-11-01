import json
from datetime import datetime
from typing import Tuple, Dict

class EthicalSafetyChecker:
    """
    Ensures all responses meet ethical standards.
    """

    # Crisis keywords for detection
    CRISIS_KEYWORDS = {
        'suicide': ['suicide', 'kill myself', 'end it all', 'no point living'],
        'self_harm': ['self-harm', 'cut myself', 'hurt myself', 'punish myself'],
        'abuse': ['abuse', 'being hurt', 'hitting me', 'attacking me'],
        'overdose': ['overdose', 'pills', 'poison', 'toxins']
    }

    def check_for_crisis(self, text: str) -> Tuple[bool, str]:
        """
        Detect crisis indicators in user text.
        Returns (is_crisis: True/False, crisis_type: str or None)
        """
        text_lower = text.lower()
        for crisis_type, keywords in self.CRISIS_KEYWORDS.items():
            if any(keyword in text_lower for keyword in keywords):
                return True, crisis_type
        return False, None

    def validate_response(self, response: str, user_input: str) -> Dict:
        """
        Check if an AI response meets ethical standards.
        Returns a dict: is_ethical, issues, severity
        """
        issues = []
        severity = 'low'

        # RULE 1: No deceptive empathy
        deceptive_phrases = [
            "i truly understand your pain",
            "i can feel what you're feeling",
            "i know exactly how you feel",
            "i've experienced this too"
        ]
        if any(phrase in response.lower() for phrase in deceptive_phrases):
            issues.append("ETHICAL_VIOLATION: Deceptive empathy detected")
            severity = 'high'

        # RULE 2: No diagnosis
        diagnostic_phrases = [
            "you have depression",
            "you have anxiety",
            "you're bipolar",
            "you have ptsd",
            "you need medication"
        ]
        if any(phrase in response.lower() for phrase in diagnostic_phrases) or "depression" in response.lower() or "medication" in response.lower():
            issues.append("ETHICAL_VIOLATION: Attempting to diagnose condition")
            severity = 'high'

        # RULE 3: Responding to crisis
        if self.check_for_crisis(user_input)[0]:
            if "professional" not in response.lower() or "988" not in response:
                issues.append("ETHICAL_VIOLATION: Not properly escalating crisis")
                severity = 'high'

        # RULE 4: No dismissiveness
        dismissive_phrases = [
            "just think positive",
            "just get over it",
            "others have it worse",
            "it's not that bad"
        ]
        if any(phrase in response.lower() for phrase in dismissive_phrases):
            issues.append("ETHICAL_VIOLATION: Dismissive response detected")
            severity = 'high'

        return {
            'is_ethical': severity != 'high',
            'issues': issues,
            'severity': severity
        }
