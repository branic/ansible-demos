"""Capture real end-of-job stats for the CLI workflow verification harness."""

import json
import os
from pathlib import Path

from ansible.executor.stats import AggregateStats
from ansible.plugins.callback import CallbackBase

DOCUMENTATION = r"""
name: capture_workflow
type: aggregate
short_description: Capture workflow artifacts for CLI verification
description:
  - Write global custom stats and per-host summaries to a JSON file.
  - Used only by this demo's CLI verification harness.
  - Set E(WORKFLOW_DEMO_CAPTURE) to the destination file path.
  - No file is written when the environment variable is unset or empty.
"""


class CallbackModule(CallbackBase):
    """Export end-of-run statistics for the CLI workflow test harness."""

    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = "aggregate"
    CALLBACK_NAME = "capture_workflow"
    CALLBACK_NEEDS_ENABLED = True

    def v2_playbook_on_stats(self, stats: AggregateStats) -> None:
        """Write artifacts and host summaries when a capture path is configured."""
        destination = os.environ.get("WORKFLOW_DEMO_CAPTURE")
        if destination:
            Path(destination).write_text(json.dumps({
                "artifacts": stats.custom.get("_run", {}),
                "hosts": {
                    host: stats.summarize(host) for host in stats.processed
                },
            }), encoding="utf-8")
