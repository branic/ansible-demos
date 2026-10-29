# Collect one asynchronous result

Collect an Ansible async job on the current host and apply a failure policy.
The caller launches the operation with `poll: 0`; the role collects its status
and handles failures. Retained caches are left to ephemeral
EE teardown or caller-managed cleanup in persistent environments.

The role is local to this demo. For broader result and error handling, see
[collect_async_status](https://github.com/redhat-cop/infra.aap_configuration/tree/devel/roles/collect_async_status).

## Inputs and output

| Variable | Type | Default | Meaning |
| --- | --- | --- | --- |
| `async_result_job` | Dictionary | Required | The complete registered launch result; must contain a nonempty string `ansible_job_id` |
| `async_result_failure_policy` | String | `fail_host` | `fail_host` or `collect_and_exclude` |
| `async_result_retries` | Integer | `40` | Positive number of status retries |
| `async_result_delay` | Integer | `1` | Positive delay between status attempts, in seconds |
| `__async_result_result` | Dictionary | Output only | Most recent collected result, including failure and retry information |

Argument specifications validate the interface; assertions validate positive
polling bounds and the job ID. Configurable defaults live in `defaults/main.yml`.
Do not set `__async_result_result`; each collection registers a fresh result. In
fail-host mode, collection output remains available through host variables after
the failure. In collection mode, an unsuccessful host ends this play before
subsequent caller tasks run.

Diagnostics display command results. Review logging before adapting the role
to operations that handle secrets.

## Usage

The [demo entrypoint](../../demonstrate-role.yml) is the complete runnable
example. After registering a launch result as `__async_timeouts_launch`, call:

```yaml
---
- name: Collect the result and apply the selected failure policy
  ansible.builtin.include_role:
    name: async_result
  vars:
    async_result_job: "{{ __async_timeouts_launch }}"
    async_result_failure_policy: collect_and_exclude
```

This is a task-list excerpt, not a standalone playbook. Run the caller with the
same connection, user, privilege context, and `ansible_async_dir` used for launch.
The caller initializes the global `__async_timeouts_failed_hosts: []` artifact
once with `set_stats`, `per_host: false`, and `aggregate: false` before calling the
role. Keep the default linear strategy, with no `serial` or job slicing.

## Failure policies

Status polling runs inside `block`/`rescue`. A completed nonzero exit, execution
timeout, missing job cache, or polling exhaustion enters rescue. The captured
result retains `msg`, `rc`, and `stderr` when available; a timeout need not have
an exit code. Failure details are visible at verbosity 0; successful results
are available at verbosity 1. Ordinary `FAILED - RETRYING` messages can appear
while a successful operation is still running: they mean the `until` condition
is not yet satisfied.

- **`fail_host`:** Fail the affected host after diagnostics.
  Other hosts can continue; any unhandled failure makes the job Failed. The
  rescued poll and deliberate final failure both appear in the recap.
- **`collect_and_exclude`:** Append the inventory hostname to the global artifact,
  then use `meta: end_host`. The original task failure is rescued, so it does not
  leave an unhandled failure or require `clear_host_errors`. Ending the host
  applies to the current play. Later jobs must explicitly exclude recorded hosts.

The role retains job caches. For cleanup, see the
[demo README](../../../README.md#cleanup-and-limitations).

If retries run out while the job is unfinished, the operation may keep running
until completion or its launch-time `async` limit. Neither `end_host` nor cache
cleanup cancels an operation. Never remove an active job's cache to cancel it.

## Limitations

The caller must guard async launches and role invocation in check mode. Run
`demonstrate-role.yml` in normal mode; it does not provide those guards.

Only one job per host per invocation is supported. The caller handles failed
launches before invoking the role. Unreachable hosts and invalid task definitions
do not enter rescue.
