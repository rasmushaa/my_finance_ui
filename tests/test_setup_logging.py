"""Basic tests for logging setup helper."""

from __future__ import annotations

import logging
import time
from pathlib import Path

import pytest

from src.core.setup_logging import setup_logging


def test_setup_logging_creates_log_file(tmp_path: Path) -> None:
    """setup_logging returns an existing log file path."""
    log_file = setup_logging(level=logging.INFO, log_dir=str(tmp_path), keep_last=5)
    assert log_file.exists()
    assert log_file.suffix == ".log"


def test_setup_logging_prunes_old_files(tmp_path: Path) -> None:
    """setup_logging keeps only the requested number of recent logs."""
    old1 = tmp_path / "old1.log"
    old2 = tmp_path / "old2.log"
    old3 = tmp_path / "old3.log"
    for file_path in (old1, old2, old3):
        file_path.write_text("old")
        time.sleep(0.01)

    setup_logging(level=logging.INFO, log_dir=str(tmp_path), keep_last=2)
    remaining = sorted(tmp_path.glob("*.log"))

    assert len(remaining) == 2


def test_setup_logging_raises_for_invalid_keep_last(tmp_path: Path) -> None:
    """keep_last must be at least one."""
    with pytest.raises(ValueError):
        setup_logging(level=logging.INFO, log_dir=str(tmp_path), keep_last=0)
