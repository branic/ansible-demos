# Collect one asynchronous result

Collect one already-launched Ansible async job on the current host and apply a
failure policy. The caller launches the operation with `poll: 0`; this role owns
status collection and error processing. Retained caches are left to ephemeral
EE teardown or caller-managed cleanup in persistent environments.

This is an intentionally small teaching role, local to this demo. It is not a
published collection or a replacement for
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
Do not set the internal `__async_result_result` variable. Each collection
registers a fresh result; it is not private in Ansible's variable model. In
fail-host mode, collection output remains available through host variables after
the failure. In collection mode, an unsuccessful host ends this play before
subsequent caller tasks run.

No secrets are accepted by this demo. Diagnostics deliberately expose command
results; add an appropriate logging policy before adapting it to sensitive work.

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

The role leaves job caches in place, including completed results. Ephemeral EE
teardown discards them. For persistent CLI environments, wait for a terminal
result and call `ansible.builtin.async_status` with the job's `jid` and
`mode: cleanup`, using the same execution context and async directory. The CLI
harness handles this outside the role.

If retries run out while the job is unfinished, the operation may keep running
until completion or its launch-time `async` limit. Neither `end_host` nor cache
cleanup cancels an operation. Never remove an active job's cache to cancel it.

## Supported execution and limitations

The demo uses POSIX local aliases, Python 3, and only `ansible.builtin`. Exact
tested versions are recorded in the [demo README](../../../README.md).
Controller tests of the earlier role used ansible-core 2.16.19 and Python 3.12.15
in the supported RHEL 9 EE. The simplified role's mixed-policy workflow outcomes
were validated in AAP; see the
[workflow comparison](../../../aap/README.md#fail-host-workflow-comparison).
The full AAP acceptance matrix has not been repeated for this version.

The role leaves check-mode handling to its caller. The demo playbook and
verification fixture skip background launches and role invocation in check mode.
Status reads report unchanged. Repeated invocations with new launches are
supported. A completed result remains readable until its cache is cleaned;
reusing a cleaned job ID fails because its result no longer exists.

Only one job per host per invocation is supported. The caller handles failed
launches before invoking the role. Unreachable hosts and invalid task definitions
do not enter rescue. The role does not normalize provider-specific API results,
cancel processes, merge parallel workflow artifacts, or recover infrastructure.
