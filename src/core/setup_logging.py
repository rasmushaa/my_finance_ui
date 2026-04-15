"""Project-wide logging setup utilities."""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path


def setup_logging(
    level: int = logging.DEBUG,
    log_dir: str = "logs",
    keep_last: int = 5,
    suppress_external: bool = True,
) -> Path:
    """Configure root logging for console and rotating timestamped files.

    Parameters
    ----------
    level : int, optional
        Logging level, for example ``logging.INFO``.
    log_dir : str, optional
        Directory where log files are written.
    keep_last : int, optional
        Number of newest log files to keep.
    suppress_external : bool, optional
        Whether noisy third-party loggers are reduced to warning level.

    Returns
    -------
    Path
        Path to the active log file for the current process.

    Raises
    ------
    ValueError
        Raised when ``keep_last`` is less than 1.
    """
    if keep_last < 1:
        raise ValueError("keep_last must be at least 1.")

    Path(log_dir).mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    logfile = Path(log_dir) / f"{timestamp}.log"

    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(filename)s:%(lineno)d "
        "%(funcName)s() [%(name)s] - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    file_handler = logging.FileHandler(logfile)
    file_handler.setFormatter(formatter)

    root = logging.getLogger()
    root.setLevel(level)
    if root.hasHandlers():
        root.handlers.clear()
    root.addHandler(console_handler)
    root.addHandler(file_handler)

    noisy_loggers = [
        "mlflow",
        "mlflow.store",
        "mlflow.store.db",
        "mlflow.store.db.utils",
        "alembic",
        "alembic.runtime",
        "alembic.runtime.migration",
        "sqlalchemy",
        "git",
        "urllib3.connectionpool",
        "google.auth._default",
        "matplotlib.font_manager",
        "pandas_gbq.gbq_connector",
        "httpx",
    ]

    if suppress_external:
        for name in noisy_loggers:
            logger = logging.getLogger(name)
            logger.handlers.clear()
            logger.setLevel(logging.WARNING)
            logger.propagate = True

    log_files = sorted(
        Path(log_dir).glob("*.log"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    for old_file in log_files[keep_last:]:
        old_file.unlink()

    return logfile
