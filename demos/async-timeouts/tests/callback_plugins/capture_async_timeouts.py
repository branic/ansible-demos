"""Capture events, recap counts, and real set_stats artifacts for CLI checks."""

import json
import os
from pathlib import Path

from ansible.executor.stats import AggregateStats
from ansible.plugins.callback import CallbackBase

DOCUMENTATION = r"""
name: capture_async_timeouts
type: aggregate
short_description: Capture async timeout demo results for local verification
description:
  - Write task results, global custom stats, and host recaps to JSON.
  - Used only by the demo verification harness.
  - Set E(ASYNC_TIMEOUTS_CAPTURE) to a destination file path to enable output.
"""


class CallbackModule(CallbackBase):
    """Record observable behavior without parsing the stdout callback format."""

    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = "aggregate"
    CALLBACK_NAME = "capture_async_timeouts"
    CALLBACK_NEEDS_ENABLED = True

    def __init__(self) -> None:
        super().__init__()
        self.events: list[dict] = []

    def _capture(self, result, status: str) -> None:
        self.events.append(
            {
                "host": result._host.get_name(),
                "task": result._task.get_name(),
                "action": result._task.action,
                "status": status,
                "result": result._result,
            }
        )

    def v2_runner_on_ok(self, result) -> None:
        """Record successful task results, including diagnostic summaries."""
        self._capture(result, "ok")

    def v2_runner_on_failed(self, result, ignore_errors: bool = False) -> None:
        """Record failures even if a subsequent rescue handles them."""
        self._capture(result, "failed")

    def v2_runner_on_skipped(self, result) -> None:
        """Record skipped tasks so check-mode behavior can be verified."""
        self._capture(result, "skipped")

    def v2_runner_on_unreachable(self, result) -> None:
        """Keep unexpected connectivity failures visible to the harness."""
        self._capture(result, "unreachable")

    def v2_playbook_on_stats(self, stats: AggregateStats) -> None:
        """Export captured events and actual end-of-job state."""
        destination = os.environ.get("ASYNC_TIMEOUTS_CAPTURE")
        if destination:
            Path(destination).write_text(
                json.dumps(
                    {
                        "events": self.events,
                        "artifacts": stats.custom.get("_run", {}),
                        "hosts": {
                            host: stats.summarize(host) for host in stats.processed
                        },
                    },
                    default=str,
                ),
                encoding="utf-8",
            )
