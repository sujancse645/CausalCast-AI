import logging
import sys
from pythonjsonlogger import jsonlogger
from app.core.middleware import request_id_var, correlation_id_var

class CorrelationIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_var.get()
        record.correlation_id = correlation_id_var.get()
        return True

def configure_logging(level: str, app_env: str = "development") -> None:
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    
    # Remove existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
        
    handler = logging.StreamHandler(sys.stdout)
    handler.addFilter(CorrelationIdFilter())
    
    if app_env == "production":
        formatter = jsonlogger.JsonFormatter(
            fmt="%(asctime)s %(levelname)s %(name)s %(message)s %(request_id)s %(correlation_id)s"
        )
    else:
        formatter = logging.Formatter(
            fmt="%(asctime)s [%(correlation_id)s] %(levelname)s %(name)s %(message)s"
        )
        
    handler.setFormatter(formatter)
    logger.addHandler(handler)
