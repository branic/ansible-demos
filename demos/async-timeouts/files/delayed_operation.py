"""A standalone, deliberately slow operation with a configurable exit status."""

import argparse
import os
from pathlib import Path
import sys
import time


def main() -> None:
    """Report the outcome after a delay; create no application resources."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--delay", type=float, required=True)
    parser.add_argument("--exit-code", type=int, required=True)
    parser.add_argument("--host", required=True)
    parser.add_argument("--pid-directory", type=Path)
    args = parser.parse_args()
    if args.delay < 0 or not 0 <= args.exit_code <= 255:
        parser.error("delay must be nonnegative and exit-code must be 0..255")
    pid_directory = args.pid_directory or os.environ.get("ASYNC_TIMEOUTS_PID_DIRECTORY")
    if pid_directory:
        # The verification harness uses this optional marker to check termination.
        (Path(pid_directory) / f"{args.host}.pid").write_text(
            str(os.getpid()), encoding="utf-8"
        )
    time.sleep(args.delay)
    if args.exit_code:
        print(
            f"Intentional operation error on {args.host}", file=sys.stderr, flush=True
        )
    else:
        print(f"Operation completed on {args.host}", flush=True)
    sys.exit(args.exit_code)


if __name__ == "__main__":
    main()
