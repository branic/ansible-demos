# Reliable Ansible automation: timeouts and reusable error handling

Demonstrate a module-specific timeout, both Ansible async polling patterns, and
centralized result collection that lets healthy hosts continue. The final demo
runs success, execution timeout, and operation error together, then compares two
host failure policies.

## Execution modes and validation

CLI verification is included. **AAP 2.7 controller and EE validation is pending**;
the AAP instructions are a lab acceptance procedure, not evidence of a completed
controller run. Separate CLI processes verify real artifact values but cannot
prove controller routing.

| Component | Requirement / validation |
| --- | --- |
| CLI ansible-core | Verified with 2.20.7; full acceptance harness passed |
| CLI Python | 3.14.8 on Linux |
| ansible-lint | Repository-pinned 26.6.0; production profile, strict |
| Lint runtime ansible-core | 2.21.5 |
| AAP | Target 2.7; controller validation pending |
| Execution environment | Existing AAP 2.7-compatible EE with Python 3 and ansible-core; tested image digest pending |
| Collections | Only `ansible.builtin`; no Galaxy installation required |
| Targets | Three local inventory aliases; no external machines or machine credentials |

The mixed role scenario took approximately **17 seconds** per CLI run in this
environment, and the URI example took 7–8 seconds. These are observed local
durations, not AAP timings. The AAP rehearsal target remains approximately
20–30 seconds per role run, excluding controller queue and startup time.

All aliases run inside the same CLI environment or AAP EE container. They
demonstrate separate Ansible host state, not independent machines. The examples
use the controller's Python interpreter and repository-local scripts; targeting
separate SSH hosts requires adapting script delivery and interpreter selection.

## Teaching sequence

| Playbook under `playbooks/` | Teaching point | Default CLI result |
| --- | --- | --- |
| `demonstrate-uri-timeout.yml` | Socket timeout followed by a successful HTTP request | Exit 0; one rescued timeout on demo1 |
| `demonstrate-positive-poll.yml` | Positive `poll` waits at the launching task | Exit 2; only demo1 continues |
| `demonstrate-separate-poll.yml` | `poll: 0`, intervening task, then explicit status polling | Exit 2; all hosts reach the intervening task; only demo1 continues |
| `demonstrate-role.yml` | Reuse collection and error processing | Depends on the selected policy |
| `verify-survivors.yml` | Brief proof of downstream exclusion | Exit 0; inherited artifact determines participating hosts |

The URI example starts a Python server on an ephemeral loopback port, requests a
three-second response with `timeout: 1`, rescues and checks that timeout, then
succeeds with `timeout: 6`. It disables HTTP proxies for these local requests and
shuts down the server in `always`. No internet service or installed web server is
needed. The fixture has a 90-second async safety limit if a job is interrupted.

`uri.timeout` is a **socket-level timeout**, not a universal overall task deadline.
`async` bounds an asynchronous task's execution, with enforcement granularity and
overhead. `retries` and `delay` govern how long status collection waits. Setting
`poll: 0` alone does not guarantee completion, success, or cleanup. See the
[URI module](https://docs.ansible.com/projects/ansible/latest/collections/ansible/builtin/uri_module.html)
and [async documentation](https://docs.ansible.com/projects/ansible/latest/playbook_guide/playbooks_async.html).

## Inventory and inputs

The structured inventory separates host identities, group settings, and per-host
scenario values. Its defaults run the standalone
[delayed command](files/delayed_operation.py) with these inputs:

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

All inputs are non-secret. Put persistent scenario changes in inventory; use
extra variables for the deliberate policy comparison and temporary controls.
`__async_timeouts_failed_hosts` is an output artifact: do not define it in
inventory, surveys, workflows, or job template variables. The role demonstration
starts a new list, rather than accumulating earlier runs. A downstream playbook
launched alone defaults to no excluded hosts.

The [role README](playbooks/roles/async_result/README.md) documents its independent
interface and read-only `__async_result_result` output. The optional
`async_timeouts_pid_directory` input is reserved for the verification harness's
process markers; normal runs create no PID marker files.

## Run with the CLI

Run from the repository root with Ansible installed. No provisioning, privilege
escalation, credentials, or external collections are needed. The URI example
needs permission to bind a local loopback socket.

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
hosts: demo1's later tasks can wait while demo2 is still being polled. A failure
policy affects only the unsuccessful host; it does not enable independent task
progression. `FAILED - RETRYING` means the `until` condition is not satisfied yet,
and can appear on a host that eventually succeeds.

Separate CLI invocations do not inherit artifacts automatically. To manually
illustrate the downstream action after the default collection run:

```bash
ansible-playbook -i demos/async-timeouts/inventory \
  demos/async-timeouts/playbooks/verify-survivors.yml \
  -e '{"__async_timeouts_failed_hosts": ["demo2", "demo3"]}'
```

This command simulates inheritance. The test harness passes the actual captured
artifact to a separate process. In AAP, launch the complete workflow instead.

For an all-success control, supply `-e async_timeouts_command_delay=0
-e async_timeouts_command_exit_code=0`. For all operation failures, use exit code
7 with delay 0. These extra variables override all three per-host values.

## Run with AAP and present

Follow [AAP configuration and validation](aap/README.md). The final comparison
uses named templates with fixed policy values. The collection workflow has one
Success-linked verification job. See the [presenter runbook](presenter.md) for
the approximately 15-minute demonstration sequence within the 45-minute content
target.

Reference [workflow host failure](../workflow-host-failure/README.md) for the
already-taught artifact and exclusion pattern. The more complete
[collect_async_status role](https://github.com/redhat-cop/infra.aap_configuration/tree/devel/roles/collect_async_status)
adds broader result and error processing; it is a reference, not a dependency.

## Verify and review good practices

Install the [repository's development tooling](../../CONTRIBUTING.md#validate-and-publish),
then run:

```bash
ansible-lint --offline --config-file .ansible-lint demos/async-timeouts
python3 demos/async-timeouts/tests/verify_cli.py
```

The harness syntax-checks every entrypoint, exercises check mode, tests both
policies with mixed/all-success/all-unsuccessful outcomes, repeats the mixed
collection scenario, and passes actual artifacts to downstream processes. It
also checks invalid role inputs, missing status, polling exhaustion, the native
examples, two HTTP runs, process termination, and terminal cache cleanup. It
uses Linux `/proc` to verify that standalone command and server processes exit.
Allow several minutes. On failure, it prints a temporary directory containing
logs and structured evidence. It does not require access to AAP.

The content follows [Good Practices for Ansible](https://redhat-cop.github.io/automation-good-practices/):
descriptive names, prefixed inputs and internal state, role defaults and argument
validation, task-only orchestration, structured inventory, appropriate debug
verbosity, explicit change reporting, and documented execution limitations.
The command is a deliberate demonstration operation with no persistent business
changes, so it reports unchanged; temporary fixture and cache mutations report
changed. Repeated runs should have identical outcome sets and leave no fixture
resources behind. Collecting an already-cleaned job ID fails by design.

The strict production lint check applies without skips or suppressions. Review
these design properties separately; a lint pass alone cannot establish them.

## Cleanup and limitations

Normal runs automatically remove terminal job caches and HTTP fixture files and
stop the HTTP server. Positive polling can finish waiting before the async
wrapper publishes its timeout; its `always` cleanup waits for that terminal
result. Cleanup polling deliberately accepts the command's failure result so
the original teaching failure remains the reported failure.

The role retains unfinished-job caches when polling is exhausted. The operation
can continue until its async limit. To clean one after it finishes, call
`ansible.builtin.async_status` with that job's `jid` and `mode: cleanup`, using the
same connection context and async directory. Never delete an active job's cache
as a way of cancelling it. The harness explicitly drains its exhaustion tests.

Cancelling an AAP job or killing a CLI process can bypass cleanup. The fixture
and commands are bounded by their async limits; inspect retained job results
before removing leftovers. Temporary files may remain after interruption.

There is no persistent target configuration or infrastructure cost. In AAP,
remove the demo workflow, six job templates, and dedicated inventory/source when
finished. Remove a project or EE registration only if dedicated to this demo.

Keep one job slice, the default linear strategy, no `serial`, no privilege
escalation, and blank limits/tags for the presentation. Unreachable hosts and
invalid task definitions do not enter rescue. Launch failures and cleanup
failures can still fail a job normally. The demo does not promise cancellation,
recovery across disconnected jobs, parallel artifact merging, or fleet-scale
performance from three local aliases.
