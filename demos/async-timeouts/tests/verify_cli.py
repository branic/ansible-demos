"""Run real Ansible processes and verify outcomes, artifacts, and cleanup."""

from dataclasses import dataclass
import json
import os
from pathlib import Path
import subprocess
import tempfile
import time

DEMO = Path(__file__).resolve().parents[1]
ROOT = DEMO.parents[1]
HOSTS = {"demo1", "demo2", "demo3"}
ARTIFACT = "__async_timeouts_failed_hosts"


def require(condition: bool, message: str) -> None:
    """Fail a check with the evidence needed to diagnose it."""
    if not condition:
        raise AssertionError(message)


@dataclass
class Job:
    """Captured execution state and its isolated working directory."""

    work: Path
    capture: dict
    elapsed: float

    def events(self, suffix: str) -> list[dict]:
        """Find tasks using their semantic name, independent of role prefixes."""
        return [
            event
            for event in self.capture["events"]
            if event["task"].endswith(suffix) and event["status"] != "skipped"
        ]


def environment(work: Path) -> dict:
    """Isolate cache files, temporary files, and the verification callback."""
    for name in ("local", "remote", "async", "fixtures", "pids"):
        (work / name).mkdir(exist_ok=True)
    return dict(
        os.environ,
        **{
            "ANSIBLE_LOCAL_TEMP": str(work / "local"),
            "ANSIBLE_REMOTE_TEMP": str(work / "remote"),
            "ANSIBLE_ASYNC_DIR": str(work / "async"),
            "ANSIBLE_ROLES_PATH": str(DEMO / "playbooks" / "roles"),
            "ANSIBLE_CALLBACK_PLUGINS": str(DEMO / "tests" / "callback_plugins"),
            "ANSIBLE_CALLBACKS_ENABLED": "capture_async_timeouts",
            "ANSIBLE_STDOUT_CALLBACK": "default",
            "ANSIBLE_NOCOLOR": "1",
            "ASYNC_TIMEOUTS_CAPTURE": str(work / "capture.json"),
            "TMPDIR": str(work / "fixtures"),
        },
    )


def run_job(
    base: Path,
    name: str,
    playbook: str,
    variables: dict | None = None,
    expected_rc: int = 0,
    flags: tuple = (),
    reuse: Job | None = None,
) -> Job:
    """Launch a separate job and capture structured evidence and elapsed time."""
    work = reuse.work if reuse else base / name
    work.mkdir(exist_ok=True)
    supplied = {"async_timeouts_pid_directory": str(work / "pids")}
    supplied.update(variables or {})
    variable_file = work / f"{name}-vars.json"
    variable_file.write_text(json.dumps(supplied), encoding="utf-8")
    command = [
        "ansible-playbook",
        "-i",
        str(DEMO / "inventory"),
        str(DEMO / playbook),
        "-e",
        f"@{variable_file}",
        *flags,
    ]
    started = time.monotonic()
    result = subprocess.run(
        command,
        cwd=ROOT,
        env=environment(work),
        capture_output=True,
        text=True,
        timeout=120,
    )
    elapsed = time.monotonic() - started
    (work / f"{name}.log").write_text(result.stdout + result.stderr, encoding="utf-8")
    require(
        result.returncode == expected_rc,
        f"{name}: expected rc={expected_rc}, got {result.returncode}\n"
        f"{result.stdout}\n{result.stderr}",
    )
    capture_file = work / "capture.json"
    require(capture_file.is_file(), f"{name}: callback did not capture results")
    job = Job(work, json.loads(capture_file.read_text(encoding="utf-8")), elapsed)
    for host, counts in job.capture["hosts"].items():
        require(
            counts["ignored"] == 0 and counts["unreachable"] == 0,
            f"{name}: ignored/unreachable failure on {host}: {counts}",
        )
    print(f"PASS: {name} ({elapsed:.1f}s)", flush=True)
    return job


def check_continuation(job: Job, task: str, expected: set[str]) -> None:
    """Assert exactly which hosts executed the actual continuation task."""
    actual = {event["host"] for event in job.events(task) if event["status"] == "ok"}
    require(actual == expected, f"{task}: expected {expected}, got {actual}")


def check_artifact(job: Job, expected: set[str]) -> None:
    """Verify actual global stats, including an initialized empty result."""
    actual = job.capture["artifacts"].get(ARTIFACT)
    require(
        isinstance(actual, list)
        and set(actual) == expected
        and len(actual) == len(expected),
        f"Incorrect artifact: {actual}",
    )


def check_recaps(job: Job, unsuccessful: set[str], collect: bool) -> None:
    """Distinguish rescued operation failures from unhandled native failures."""
    for host, counts in job.capture["hosts"].items():
        require(
            counts["rescued"] == int(host in unsuccessful),
            f"Incorrect rescued count for {host}: {counts}",
        )
        require(
            counts["failures"] == int(host in unsuccessful and not collect),
            f"Incorrect unhandled failure count for {host}: {counts}",
        )


def process_running(pid: int) -> bool:
    """Treat exited Linux zombies as stopped processes."""
    status = Path(f"/proc/{pid}/stat")
    try:
        return status.read_text(encoding="utf-8").split(")", 1)[1].split()[0] != "Z"
    except FileNotFoundError:
        return False


def check_cleanup(job: Job) -> None:
    """Verify both cache removal and termination of the standalone commands."""
    require(not list((job.work / "async").iterdir()), f"Cache remains in {job.work}")
    pids = [
        int(path.read_text(encoding="utf-8"))
        for path in (job.work / "pids").glob("*.pid")
    ]
    deadline = time.monotonic() + 3
    while any(process_running(pid) for pid in pids) and time.monotonic() < deadline:
        time.sleep(0.1)
    require(
        not any(process_running(pid) for pid in pids),
        f"A delayed command is still running: {pids}",
    )


def check_mixed(base: Path, policy: str, label: str) -> None:
    """Check all three outcomes and optionally execute real artifact handoff."""
    collect = policy == "collect_and_exclude"
    job = run_job(
        base,
        label,
        "playbooks/demonstrate-role.yml",
        {"async_timeouts_failure_policy": policy},
        0 if collect else 2,
    )
    check_continuation(job, "Continue on hosts whose operation succeeded", {"demo1"})
    check_recaps(job, {"demo2", "demo3"}, collect)
    check_artifact(job, {"demo2", "demo3"} if collect else set())
    summaries = {
        event["host"]: event["result"]["msg"]
        for event in job.events("Collect | Display the result summary")
    }
    require(summaries["demo1"]["return_code"] == 0, "Success result lost")
    require(
        summaries["demo2"]["finished"] and "Timeout" in summaries["demo2"]["message"],
        "Execution timeout lost",
    )
    require(
        summaries["demo3"]["return_code"] == 7
        and "Intentional operation error" in summaries["demo3"]["stderr"],
        "Operation failure diagnostics lost",
    )
    launched = job.events(
        "Launch operation | Start the standalone command in the background"
    )
    require(len(launched) == 3, "Not all hosts launched their commands")
    require(
        len(list((job.work / "pids").glob("*.pid"))) == 3,
        "Standalone commands did not publish termination-check markers",
    )
    check_cleanup(job)
    if collect:
        downstream = run_job(
            base,
            f"{label}-downstream",
            "playbooks/verify-survivors.yml",
            job.capture["artifacts"],
        )
        check_continuation(
            downstream, "Show which hosts performed the downstream action", {"demo1"}
        )


def check_controls(base: Path) -> None:
    """Exercise empty and complete exclusion sets under each policy."""
    for policy in ("fail_host", "collect_and_exclude"):
        for exit_code in (0, 7):
            collect = policy == "collect_and_exclude"
            failed = HOSTS if exit_code else set()
            label = f"control-{policy}-rc{exit_code}"
            job = run_job(
                base,
                label,
                "playbooks/demonstrate-role.yml",
                {
                    "async_timeouts_failure_policy": policy,
                    "async_timeouts_command_delay": 0,
                    "async_timeouts_command_exit_code": exit_code,
                },
                2 if failed and not collect else 0,
            )
            check_recaps(job, failed, collect)
            check_artifact(job, failed if collect else set())
            check_continuation(
                job, "Continue on hosts whose operation succeeded", HOSTS - failed
            )
            check_cleanup(job)
            if collect:
                downstream = run_job(
                    base,
                    f"{label}-downstream",
                    "playbooks/verify-survivors.yml",
                    job.capture["artifacts"],
                )
                check_continuation(
                    downstream,
                    "Show which hosts performed the downstream action",
                    HOSTS - failed,
                )


def check_role_edges(base: Path) -> None:
    """Reject bad inputs and distinguish missing status from unfinished work."""
    fixture = "tests/playbooks/verify-role-inputs.yml"
    invalid = [
        {},
        {"async_result_job": {}},
        {"async_result_job": {"ansible_job_id": ""}},
        {
            "async_result_job": {"ansible_job_id": "missing"},
            "async_result_failure_policy": "invalid",
        },
        {"async_result_job": {"ansible_job_id": "missing"}, "async_result_retries": 0},
        {"async_result_job": {"ansible_job_id": "missing"}, "async_result_delay": -1},
    ]
    for index, variables in enumerate(invalid):
        job = run_job(
            base, f"invalid-input-{index}", fixture, variables, 2, ("--limit", "demo1")
        )
        require(
            not job.events("Collect | Wait for a terminal job result"),
            "Invalid inputs reached status polling",
        )
        require(
            job.capture["hosts"]["demo1"]["failures"] == 1, "Invalid input did not fail"
        )
        check_cleanup(job)
    for policy in ("fail_host", "collect_and_exclude"):
        collect = policy == "collect_and_exclude"
        job = run_job(
            base,
            f"missing-status-{policy}",
            fixture,
            {
                "async_result_job": {"ansible_job_id": "999999999999.1"},
                "async_result_failure_policy": policy,
            },
            0 if collect else 2,
            ("--limit", "demo1"),
        )
        check_recaps(job, {"demo1"}, collect)
        check_artifact(job, {"demo1"} if collect else set())
        check_cleanup(job)

    for policy in ("fail_host", "collect_and_exclude"):
        collect = policy == "collect_and_exclude"
        job = run_job(
            base,
            f"poll-exhaustion-{policy}",
            "playbooks/demonstrate-role.yml",
            {
                "async_timeouts_command_delay": 15,
                "async_timeouts_command_exit_code": 0,
                "async_timeouts_execution_timeout": 30,
                "async_timeouts_poll_retries": 1,
                "async_timeouts_failure_policy": policy,
            },
            0 if collect else 2,
            ("--limit", "demo1"),
        )
        check_recaps(job, {"demo1"}, collect)
        check_continuation(job, "Continue on hosts whose operation succeeded", set())
        check_artifact(job, {"demo1"} if collect else set())
        require(
            job.events("Collect | Explain an unfinished job"),
            "Unfinished-job warning absent",
        )
        launch = job.events(
            "Launch operation | Start the standalone command in the background"
        )[0]["result"]
        require(Path(launch["results_file"]).is_file(), "Running-job cache was deleted")
        pid = int((job.work / "pids" / "demo1.pid").read_text(encoding="utf-8"))
        require(
            process_running(pid), "The exhaustion scenario did not leave work running"
        )
        run_job(
            base,
            f"drain-{policy}",
            "tests/playbooks/clean-test-job.yml",
            {"async_timeouts_cleanup_job": launch},
            flags=("--limit", "demo1"),
            reuse=job,
        )
        check_cleanup(job)


def check_examples(base: Path) -> None:
    """Run the native examples and verify the self-contained HTTP lifecycle."""
    for mode in ("positive", "separate"):
        job = run_job(
            base,
            f"native-{mode}",
            f"playbooks/demonstrate-{mode}-poll.yml",
            expected_rc=2,
        )
        task = (
            "Show that the launching task completed before continuing"
            if mode == "positive"
            else "Show that only successful hosts continue after collection"
        )
        check_continuation(job, task, {"demo1"})
        require(
            {
                host
                for host, counts in job.capture["hosts"].items()
                if counts["failures"]
            }
            == {"demo2", "demo3"},
            "Native example failures differ",
        )
        if mode == "separate":
            check_continuation(
                job, "Demonstrate work between launch and collection", HOSTS
            )
        check_cleanup(job)

    for iteration in range(2):
        job = run_job(base, f"uri-{iteration}", "playbooks/demonstrate-uri-timeout.yml")
        require(
            job.capture["hosts"]["demo1"]["rescued"] == 1,
            "Expected URI timeout not rescued",
        )
        require(
            job.events("Confirm the expected socket timeout was the failure")
            and job.events("Verify the successful response"),
            "URI outcomes not verified",
        )
        state = job.events("Remember the fixture endpoint")[0]["result"][
            "ansible_facts"
        ]["__async_timeouts_http_state"]
        require(not process_running(state["pid"]), "HTTP fixture still running")
        fixture_path = job.events("Create a private directory for the HTTP fixture")[0][
            "result"
        ]["path"]
        require(not Path(fixture_path).exists(), "HTTP fixture directory remains")
        check_cleanup(job)


def check_static_and_check_mode(base: Path) -> None:
    """Check all entrypoints and prove check mode does not launch operations."""
    playbooks = sorted((DEMO / "playbooks").glob("*.yml"))
    playbooks += sorted((DEMO / "tests" / "playbooks").glob("*.yml"))
    for index, playbook in enumerate(playbooks):
        relative = str(playbook.relative_to(DEMO))
        work = base / f"syntax-{index}"
        work.mkdir()
        result = subprocess.run(
            [
                "ansible-playbook",
                "-i",
                str(DEMO / "inventory"),
                str(playbook),
                "--syntax-check",
            ],
            cwd=ROOT,
            env=environment(work),
            capture_output=True,
            text=True,
            timeout=30,
        )
        require(
            result.returncode == 0, f"Syntax check failed: {relative}\n{result.stderr}"
        )
        job = run_job(
            base,
            f"check-mode-{index}",
            relative,
            {"async_result_job": {"ansible_job_id": "unused"}},
            flags=("--check",),
        )
        mutations = [
            event
            for event in job.capture["events"]
            if event["status"] != "skipped"
            and event["action"]
            in {
                "ansible.builtin.command",
                "ansible.builtin.async_status",
                "ansible.builtin.uri",
                "ansible.builtin.tempfile",
                "ansible.builtin.file",
                "ansible.builtin.set_stats",
            }
        ]
        require(not mutations, f"Check mode attempted execution: {mutations}")
        check_cleanup(job)


def main() -> None:
    """Run the acceptance matrix using the active ansible-playbook executable."""
    with tempfile.TemporaryDirectory(
        prefix="async-timeouts-verification-"
    ) as directory:
        base = Path(directory)
        try:
            check_static_and_check_mode(base)
            check_mixed(base, "fail_host", "mixed-fail-host")
            check_mixed(base, "collect_and_exclude", "mixed-collect")
            check_mixed(base, "collect_and_exclude", "mixed-collect-repeat")
            check_controls(base)
            check_role_edges(base)
            check_examples(base)
        except Exception:
            # Preserve logs after a failing assertion, without leaving live work.
            import shutil

            destination = Path(tempfile.mkdtemp(prefix="async-timeouts-failure-"))
            shutil.copytree(base, destination, dirs_exist_ok=True)
            print(f"Failure evidence copied to {destination}", flush=True)
            raise
        finally:
            # Let bounded wrappers finish before removing their cache directories.
            deadline = time.monotonic() + 100
            pids = [
                int(path.read_text(encoding="utf-8"))
                for path in base.glob("*/pids/*.pid")
            ]
            while (
                any(process_running(pid) for pid in pids)
                and time.monotonic() < deadline
            ):
                time.sleep(0.2)
    print("All CLI checks passed. AAP routing still requires controller validation.")


if __name__ == "__main__":
    main()
