import logging
import os
from datetime import datetime
import json
from eddie.evaluation import get_system_usage

class JsonFormatter(logging.Formatter):
    def format(self, record):
        system_usage = get_system_usage()  
        log_record = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "level": record.levelname,
            "operation": getattr(record, "operation", "UNKNOWN"),
            "response_time": getattr(record, "response_time", None),
            "clarity_score": getattr(record, "clarity_score", None),
            "accuracy_score": getattr(record, "accuracy_score", None),
            "status": getattr(record, "status", None),
            "description": record.getMessage(),
            "cpu": system_usage.get("cpu", None),         
            "memory": system_usage.get("memory", None),    
            "gpu": system_usage.get("gpu", None),          
        }
        return json.dumps(log_record)

def get_logger(name="performance_logger"):
    logger = logging.getLogger(name)
    logger.propagate = False  # Root logger'a aktarılmasın
    if not logger.handlers:  # Handler zaten eklenmişse tekrar ekleme
        logger.setLevel(logging.DEBUG)
        base_dir = os.path.join(os.path.expanduser("~"), "EddieApp", "logs")
        os.makedirs(base_dir, exist_ok=True)
        log_path = os.path.join(base_dir, "system_log.jsonl")
        file_handler = logging.FileHandler(log_path, encoding='utf-8')
        file_handler.setFormatter(JsonFormatter())
        logger.addHandler(file_handler)

    return logger