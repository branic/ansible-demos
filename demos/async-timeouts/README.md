# Ansible timeouts and reusable error handling

Compare a module-specific timeout, two Ansible async polling patterns, and a
reusable role for result collection and error handling. The role example runs
successful, timed-out, and failed operations together, then compares two host
failure policies.

## Execution modes and requirements

Run with the **CLI or AAP**.

| Component | Requirement |
| --- | --- |
| Ansible (CLI and EE) | 2.16+ |
| AAP | 2.7 |
| Collections | None |
| Targets | Inventory aliases: `demo1`, `demo2`, `demo3` |
| URI endpoint | HTTPS access to `httpbin.org` |

## Teaching sequence

| Playbook under `playbooks/` | Teaching point | Default CLI result |
| --- | --- | --- |
| `demonstrate-uri-timeout.yml` | Socket timeout followed by a successful HTTP request | Exit 0; one rescued timeout on demo1 |
| `demonstrate-positive-poll.yml` | Positive `poll` waits at the launching task | Exit 2; only demo1 continues |
| `demonstrate-separate-poll.yml` | `poll: 0`, intervening task, then explicit status polling | Exit 2; all hosts reach the intervening task; only demo1 continues |
| `demonstrate-role.yml` | Reuse collection and error processing | Depends on the selected policy |
| `verify-survivors.yml` | Verify downstream exclusion | Exit 0; inherited artifact determines participating hosts |

The URI example calls [httpbin's three-second delay endpoint](https://httpbin.org/delay/3)
with `timeout: 1`, rescues and displays the failure, then succeeds with `timeout: 6`.

`uri.timeout` is a **socket-level timeout**, not a universal overall task deadline.
`async` limits an asynchronous task's execution; enforcement and collection add
overhead. `retries` and `delay` control status collection. Setting
`poll: 0` alone does not guarantee completion, success, or cleanup. See the
[URI module](https://docs.ansible.com/projects/ansible/latest/collections/ansible/builtin/uri_module.html)
and [async documentation](https://docs.ansible.com/projects/ansible/latest/playbook_guide/playbooks_async.html).

## Inventory and inputs

The inventory defines these per-host defaults for the
[delayed command](files/delayed_operation.py) executed by the async playbooks:

| Host | Delay | Exit code | Observed outcome |
| --- | --- | --- | --- |
| demo1 | 3 seconds | 0 | Success |
| demo2 | 60 seconds | 0 if allowed to finish | Killed by the async execution limit |
| demo3 | 3 seconds | 7 | Intentional operation error, with stderr |

| Variable | Default | Purpose |
| --- | --- | --- |
| `async_timeouts_command_delay` | Per-host table above | Standalone command sleep, in seconds |
| `async_timeouts_command_exit_code` | Per-host table above | Standalone command exit status |
| `async_timeouts_execution_timeout` | `10` | Launch-time async execution limit, in seconds |
| `async_timeouts_poll_interval` | `1` | Positive poll interval or explicit status retry delay |
| `async_timeouts_poll_retries` | `40` | Explicit status retry count |
| `async_timeouts_failure_policy` | `fail_host` | `fail_host` or `collect_and_exclude` for the role example |
| `async_timeouts_http_url` | `https://httpbin.org/delay/3` | Delayed-response endpoint for the URI example |

All inputs are non-secret. Put persistent scenario changes in inventory; use
extra variables for policy comparisons and temporary controls.

See the [role README](playbooks/roles/async_result/README.md) for inputs and outputs.

## Run with the CLI

Run from the repository root.

```bash
ansible-playbook -i demos/async-timeouts/inventory \
  demos/async-timeouts/playbooks/demonstrate-uri-timeout.yml

ansible-playbook -i demos/async-timeouts/inventory \
  demos/async-timeouts/playbooks/demonstrate-positive-poll.yml

ansible-playbook -i demos/async-timeouts/inventory \
  demos/async-timeouts/playbooks/demonstrate-separate-poll.yml

ansible-playbook -i demos/async-timeouts/inventory \
  demos/async-timeouts/playbooks/demonstrate-role.yml

ansible-playbook -i demos/async-timeouts/inventory \
  demos/async-timeouts/playbooks/demonstrate-role.yml \
  -e async_timeouts_failure_policy=collect_and_exclude
```

The native async examples and fail-host role run intentionally exit **2**. In
collection mode, the role run exits **0**, exports demo2 and demo3, and prints
`ROLE continued on demo1`. Those unsuccessful hosts have `rescued=1`, `failed=0`,
and `ignored=0`. In fail-host mode, each has an additional unhandled failure.

Ansible's default linear strategy waits for the current task across participating
hosts, so demo1 can wait while demo2 is polled. A failure policy does not change
that scheduling. `FAILED - RETRYING` means the `until` condition is not yet
satisfied and can appear on a host that eventually succeeds.

Separate CLI invocations do not inherit artifacts automatically. To manually
illustrate the downstream action after the default collection run:

```bash
ansible-playbook -i demos/async-timeouts/inventory \
  demos/async-timeouts/playbooks/verify-survivors.yml \
  -e '{"__async_timeouts_failed_hosts": ["demo2", "demo3"]}'
```

This command simulates inheritance. In AAP, launch the complete workflow.

## Run with AAP

Follow the [AAP setup instructions](aap/README.md). The final comparison
uses two workflows with the same Success-linked verification job:
`demo_workflow_async_fail_host` fails before verification can run, while
`demo_workflow_async_collect_and_exclude` succeeds and verifies only demo1.
Their start templates have fixed policy values.

See [workflow host failure](../workflow-host-failure/README.md) for the artifact
and exclusion pattern. The
[collect_async_status role](https://github.com/redhat-cop/infra.aap_configuration/tree/devel/roles/collect_async_status)
adds broader result and error processing; it is a reference, not a dependency.

## Verify

Install the [repository's development tooling](../../CONTRIBUTING.md#validate-and-publish),
then run:

```bash
ansible-lint --offline --config-file .ansible-lint demos/async-timeouts
python3 demos/async-timeouts/tests/verify_cli.py
```

## Cleanup and limitations

Run the async examples in normal mode; they do not support check mode.

Async job caches are discarded when an ephemeral EE is removed. For CLI runs,
wait for the job to finish, then remove retained caches with
`ansible.builtin.async_status`, using its `jid` and `mode: cleanup` in the same
execution context. Polling exhaustion and cache cleanup do not cancel a running
operation.

In AAP, remove both workflows, six job templates, and the dedicated inventory/source.
Remove project and EE registrations only if dedicated to this demo.
