class BiasDetector:
    """
    Identifies potential gender and cultural biases in responses.
    Flexible matching for singular/plural and keyword variations.
    """

    def __init__(self):
        # Masculine/feminine keywords for bias detection
        self.masculine_terms = ["man", "men", "boy", "boys", "male", "males"]
        self.feminine_terms = ["woman", "women", "girl", "girls", "female", "females"]
        self.strength_terms = ["strong", "tough", "brave", "aggressive"]
        self.emotion_terms = ["emotional", "sensitive", "weak", "fragile"]

        # Cultural assumptions (Western-centric features, etc.)
        self.cultural_assumptions = [
            "you should tell your family",   # Family involvement isn't universal
            "western therapy approach",      # Western-centric
            "individual achievement",        # Implies individualism
        ]

    def check_gender_bias(self, response: str):
        response_lower = response.lower()
        biased = False
        issue = None

        # Masculine: "man"/"men" + "strong"/"tough"/etc.
        if any(m in response_lower for m in self.masculine_terms) and any(s in response_lower for s in self.strength_terms):
            biased = True
            issue = "Masculine strength stereotype detected"

        # Feminine: "woman"/"women" + "emotional"/"weak"/etc.
        if any(f in response_lower for f in self.feminine_terms) and any(e in response_lower for e in self.emotion_terms):
            biased = True
            issue = "Feminine emotion/weakness stereotype detected"

        return {
            'biased': biased,
            'type': 'gender_stereotype' if biased else None,
            'issue': issue
        }

    def check_cultural_sensitivity(self, response: str):
        response_lower = response.lower()
        issues = []
        for assumption in self.cultural_assumptions:
            if assumption in response_lower:
                issues.append(f"Potential cultural assumption: {assumption}")
        return {
            'culturally_sensitive': len(issues) == 0,
            'issues': issues
        }

    def full_bias_check(self, response: str):
        gender_result = self.check_gender_bias(response)
        cultural_result = self.check_cultural_sensitivity(response)
        return {
            'passed_ethical_check': not gender_result['biased'] and cultural_result['culturally_sensitive'],
            'gender_bias': gender_result,
            'cultural_sensitivity': cultural_result
        }
