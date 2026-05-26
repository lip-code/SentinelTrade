"""loguru logging configuration for SentinelTrade."""
import sys
from pathlib import Path

from loguru import logger


def setup_logger(
    level: str = "DEBUG",
    rotation: str = "1 day",
    retention: str = "30 days",
    log_dir: str = "data/logs",
) -> None:
    """Configure loguru with console, file, error, and risk log handlers."""
    logger.remove()

    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)

    logger.add(
        sys.stdout,
        level=level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> | <level>{message}</level>",
        colorize=True,
    )

    logger.add(
        str(log_path / "sentinel_{time:YYYY-MM-DD}.log"),
        level="DEBUG",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
        rotation=rotation,
        retention=retention,
        encoding="utf-8",
    )

    logger.add(
        str(log_path / "error_{time:YYYY-MM-DD}.log"),
        level="ERROR",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
        rotation=rotation,
        retention=retention,
        encoding="utf-8",
    )

    logger.add(
        str(log_path / "risk_{time:YYYY-MM-DD}.log"),
        level="INFO",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {message}",
        rotation=rotation,
        retention=retention,
        encoding="utf-8",
        filter=lambda record: "risk" in record["extra"].get("module", ""),
    )
