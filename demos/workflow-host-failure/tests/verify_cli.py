"""Exercise separate jobs and pass actual set_stats artifacts between them."""

import json
import os
from pathlib import Path
import subprocess
import tempfile


DEMO = Path(__file__).resolve().parents[1]
ROOT = DEMO.parents[1]
ALL_HOSTS = ["demo1", "demo2", "demo3"]


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def run_job(work, name, variables, expected_rc=0):
    capture = work / "stats.json"
    capture.unlink(missing_ok=True)
    extra_vars = work / "extra-vars.json"
    extra_vars.write_text(json.dumps(variables))
    env = dict(os.environ)
    env.update({
        "ANSIBLE_LOCAL_TEMP": str(work / "local"),
        "ANSIBLE_REMOTE_TEMP": str(work / "remote"),
        "ANSIBLE_CALLBACK_PLUGINS": str(DEMO / "tests" / "callback_plugins"),
        "ANSIBLE_CALLBACKS_ENABLED": "capture_workflow",
        "ANSIBLE_STDOUT_CALLBACK": "default",
        "ANSIBLE_NOCOLOR": "1",
        "WORKFLOW_DEMO_CAPTURE": str(capture),
    })
    command = ["ansible-playbook", "-i", str(DEMO / "inventory" / "demo.yml")]
    command.extend([str(DEMO / "playbooks" / f"{name}.yml"), "-e", f"@{extra_vars}"])
    result = subprocess.run(
        command,
        cwd=ROOT, env=env, capture_output=True, text=True, timeout=90,
    )
    require(result.returncode == expected_rc,
            f"{name}: expected rc={expected_rc}, got {result.returncode}\n"
            f"{result.stdout}\n{result.stderr}")
    require(capture.is_file(), f"{name}: missing stats\n{result.stdout}")
    return json.loads(capture.read_text()), result.stdout


def check_messages(output, prefix, expected):
    for host in ALL_HOSTS:
        require((f"{prefix} {host}" in output) == (host in expected),
                f"Incorrect action target for {prefix}: {host}\n{output}")


def check_rescues(stats, failed):
    for host, counts in stats["hosts"].items():
        require(counts["failures"] == 0 and counts["ignored"] == 0,
                f"Unexpected unhandled or ignored failure on {host}: {counts}")
        require(counts["rescued"] == int(host in failed),
                f"Incorrect rescue count on {host}: {counts}")


def check_chain(work, label, failed, configure_failed):
    inputs = {
        "workflow_host_failure_initial_fail_hosts": failed,
        "workflow_host_failure_configure_fail_hosts": configure_failed,
    }
    first_hosts = set(ALL_HOSTS) - set(failed)
    new_failures = first_hosts & set(configure_failed)
    all_failed = set(failed) | new_failures
    second_hosts = set(ALL_HOSTS) - all_failed

    first, output = run_job(work, "demo", inputs)
    require(set(first["artifacts"]["__workflow_host_failure_failed_hosts"]) == set(failed),
            f"{label}: incorrect first artifact: {first}")
    check_messages(output, "STAGE 1 succeeded on", first_hosts)
    check_messages(output, "STAGE 1 continued on", first_hosts)
    check_rescues(first, set(failed))

    second, output = run_job(work, "configure", inputs | first["artifacts"])
    exported = second["artifacts"]["__workflow_host_failure_failed_hosts"]
    require(set(exported) == all_failed and len(exported) == len(all_failed),
            f"{label}: failures were lost or duplicated: {second}")
    check_messages(output, "STAGE 2 configured", second_hosts)
    check_rescues(second, new_failures)

    # The nearest parent's artifact replaces the same key from an earlier job.
    third, output = run_job(work, "verify", inputs | first["artifacts"] | second["artifacts"])
    check_messages(output, "STAGE 3 verified", second_hosts)
    check_rescues(third, set())
    print(f"PASS: {label}")


def main():
    with tempfile.TemporaryDirectory(prefix="workflow-host-failure-") as directory:
        work = Path(directory)
        check_chain(work, "one host fails", ["demo2"], [])
        check_chain(work, "all hosts succeed", [], [])
        check_chain(work, "multiple hosts fail", ["demo1", "demo3"], [])
        check_chain(work, "another host fails in stage two", ["demo2"], ["demo3"])
        check_chain(work, "all hosts fail in stage one", ALL_HOSTS, [])
        check_chain(work, "all remaining hosts fail in stage two", ["demo2"], ["demo1", "demo3"])
        check_chain(work, "an already failed host is not retried", ["demo2"], ["demo2"])
        for job, prefix in [("configure", "STAGE 2 configured"), ("verify", "STAGE 3 verified")]:
            stats, output = run_job(work, job, {})
            check_messages(output, prefix, set(ALL_HOSTS))
            check_rescues(stats, set())
            print(f"PASS: standalone {job} defaults to no failed hosts")
    print("All CLI checks passed.")


if __name__ == "__main__":
    main()
