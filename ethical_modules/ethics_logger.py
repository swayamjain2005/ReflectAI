import json
import logging
from datetime import datetime
from pythonjsonlogger import jsonlogger

class EthicsLogger:
    """
    Maintains audit trail for all ethical decisions and safety events.
    Logs are persistent and human-readable.
    """

    def __init__(self, log_file='logs/ethics_audit.log'):
        self.logger = logging.getLogger('ethics_audit')
        self.logger.setLevel(logging.INFO)

        # JSON formatter for readable logs
        logHandler = logging.FileHandler(log_file)
        formatter = jsonlogger.JsonFormatter()
        logHandler.setFormatter(formatter)
        if not self.logger.hasHandlers():
            self.logger.addHandler(logHandler)

    def log_crisis_detection(self, user_id: str, crisis_type: str, user_text_length: int):
        self.logger.info(
            'crisis_detected',
            extra={
                'user_id': user_id,
                'crisis_type': crisis_type,
                'timestamp': datetime.now().isoformat(),
                'user_text_length': user_text_length
            }
        )

    def log_ethical_violation(self, user_id: str, violation_type: str, details: str):
        self.logger.warning(
            'ethical_violation_detected',
            extra={
                'user_id': user_id,
                'violation_type': violation_type,
                'details': details,
                'timestamp': datetime.now().isoformat()
            }
        )

    def log_data_access(self, user_id: str, action: str):
        self.logger.info(
            'data_access',
            extra={
                'user_id': user_id,
                'action': action,  # 'read', 'write', 'delete'
                'timestamp': datetime.now().isoformat()
            }
        )

    def log_bias_detection(self, bias_type: str, severity: str):
        self.logger.info(
            'bias_detected',
            extra={
                'bias_type': bias_type,
                'severity': severity,
                'timestamp': datetime.now().isoformat()
            }
        )
