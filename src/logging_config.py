from __future__ import annotations

import logging
from typing import Final


DEFAULT_LOG_LEVEL: Final[str] = "INFO"


def setup_logging(level: str | None = None) -> None:
    """
    Configura logging básico do projeto.

    - Se você quer deixar o log mais verboso (debug), chame:
      `setup_logging("DEBUG")` logo no início do seu script.
    """
    log_level = (level or DEFAULT_LOG_LEVEL).upper()

    logging.basicConfig(
        level=getattr(logging, log_level, logging.INFO),
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )

