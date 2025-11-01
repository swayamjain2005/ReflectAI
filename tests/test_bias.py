import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from ethical_modules.bias_detector import BiasDetector

def test_gender_bias():
    detector = BiasDetector()
    response = "Men are naturally strong and women are emotional"
    result = detector.full_bias_check(response)
    assert result['passed_ethical_check'] == False
    print("✅ Gender bias detection working")

def test_no_bias():
    detector = BiasDetector()
    response = "Everyone experiences emotions and strength differently."
    result = detector.full_bias_check(response)
    assert result['passed_ethical_check'] == True
    print("✅ No bias in neutral statement")

if __name__ == "__main__":
    test_gender_bias()
    test_no_bias()
