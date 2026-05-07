from loguru import logger
import os

os.makedirs("logs", exist_ok=True)

logger.add(
    "logs/ai_system.log",
    rotation="1 MB",
    retention="7 days",
    level="INFO",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}"
)

