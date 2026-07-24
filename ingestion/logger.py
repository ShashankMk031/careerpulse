"""
Logger module for CareerPulse.
Responsible for setting up structured logging and providing the reusable logger and adapters.
"""

import logging
from typing import Any, Tuple

# Basic logging configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger("CareerPulse")

class PipelineLoggerAdapter(logging.LoggerAdapter):
    """
    LoggerAdapter that automatically prepends the Pipeline Execution ID
    to every log message for trace correlating.
    """
    def process(self, msg: str, kwargs: Any) -> Tuple[str, Any]:
        pipeline_id = self.extra.get("pipeline_id", "SYSTEM")
        return f"Pipeline ID: {pipeline_id} | {msg}", kwargs
