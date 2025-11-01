import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
# ...your imports here...

from ethical_modules.ethics_logger import EthicsLogger

def test_logging():
    logger = EthicsLogger(log_file='logs/test_ethics_audit.log')
    logger.log_crisis_detection(user_id="user1", crisis_type="suicide", user_text_length=44)
    logger.log_ethical_violation(user_id="user1", violation_type="deceptive_empathy", details="Tried to claim feelings.")
    logger.log_data_access(user_id="user1", action="write")
    logger.log_bias_detection(bias_type="gender_stereotype", severity="medium")
    print("✅ Ethics Logger ran without errors (check logs/test_ethics_audit.log for output)")

if __name__ == "__main__":
    test_logging()
