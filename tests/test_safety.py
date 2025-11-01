import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from ethical_modules.safety_checker import EthicalSafetyChecker

def test_crisis_detection():
    checker = EthicalSafetyChecker()
    is_crisis, crisis_type = checker.check_for_crisis("I want to kill myself")
    assert is_crisis == True
    assert crisis_type == 'suicide'
    print("✅ Crisis detection working")

def test_deceptive_empathy_detection():
    checker = EthicalSafetyChecker()
    response = "I truly understand your pain and can feel what you're feeling"
    validation = checker.validate_response(response, "I'm sad")
    assert validation['is_ethical'] == False
    print("✅ Deceptive empathy detection working")

def test_diagnosis_prevention():
    checker = EthicalSafetyChecker()
    response = "You have clinical depression and need medication"
    validation = checker.validate_response(response, "I feel sad lately")
    assert validation['is_ethical'] == False
    print("✅ Diagnosis detection working")

def test_dismissiveness():
    checker = EthicalSafetyChecker()
    response = "Just think positive and get over it"
    validation = checker.validate_response(response, "I'm anxious")
    assert validation['is_ethical'] == False
    print("✅ Dismissive response detection working")

if __name__ == "__main__":
    test_crisis_detection()
    test_deceptive_empathy_detection()
    test_diagnosis_prevention()
    test_dismissiveness()
