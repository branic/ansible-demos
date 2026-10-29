# Reliable Ansible automation: timeouts and reusable error handling

Demonstrate a module-specific timeout, both Ansible async polling patterns, and
centralized result collection that lets healthy hosts continue. The final demo
runs success, execution timeout, and operation error together, then compares two
host failure policies.

## Execution modes and validation

Supports **both CLI and AAP 2.7**. The CLI acceptance harness passed, and actual
controller runs verified the examples, both policies, artifact inheritance,
Success-link routing, repeat runs, controls, and check mode. See the
[AAP validation record](aap/README.md#completed-lab-validation) for job IDs and
the exact tested revision and execution environment.

| Component | Requirement / validation |
| --- | --- |
| CLI ansible-core | Verified with 2.20.7; full acceptance harness passed |
| CLI Python | 3.14.8 on Linux |
| ansible-lint | Repository-pinned 26.6.0; production profile, strict |
| Lint runtime ansible-core | 2.21.5 |
| AAP | Verified with 2.7.20261019; automation controller 4.8.12 |
| Execution environment | Supported RHEL 9 EE; ansible-core 2.16.19, Python 3.12.15, RHEL 9.8; pinned image digest in the AAP validation record |
| Collections | Only `ansible.builtin`; no Galaxy installation required |
| Targets | Three local inventory aliases; no external machines or machine credentials |
| URI endpoint | Standalone container on OpenShift; see [service setup](service/README.md) |

The mixed role scenario took approximately **17 seconds** per CLI run and
**20 seconds** per AAP job. The complete AAP collection-and-verification workflow
took approximately **24–25 seconds**. The simplified URI lesson took approximately
**5 seconds** against the local test server and **8 seconds** against the
OpenShift service in AAP. Controller elapsed time excludes queue time but
includes some runner setup; these are lab observations, not fleet-scale timing
guarantees.

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

The URI example calls a [standalone HTTP service](service/README.md) prepared
before the lesson. It requests a three-second response with `timeout: 1`, rescues
and displays the failure, then succeeds with `timeout: 6`. Outcome assertions
live in the CLI harness, which verifies the timeout and response content and
rejects a fast endpoint as an invalid demonstration. The teaching playbook
contains no server setup, async launch, or teardown. The service is one Python
container on OpenShift; no VM or separately managed machine is required.

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
| `async_timeouts_http_url` | ClusterIP URL documented in [service setup](service/README.md#endpoints) | Complete URI lesson URL, including `/slow`; use the Route URL for CLI access |

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

Run from the repository root with Ansible installed. The async examples need no
provisioning, privilege escalation, credentials, or external collections. For
the URI lesson, [deploy the HTTP service](service/README.md#deploy) first using
`oc`, then obtain its Route hostname. Deployment, cleanup, and Route lookup use
cluster credentials; the teaching playbooks need no machine or OpenShift
credentials.

```bash
async_timeouts_route=$(oc -n async-timeouts-demo get route async-timeouts-http -o jsonpath='{.spec.host}')
ansible-playbook -i demos/async-timeouts/inventory \
  demos/async-timeouts/playbooks/demonstrate-uri-timeout.yml \
  -e "async_timeouts_http_url=http://${async_timeouts_route}/slow"

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
examples, repeated HTTP runs, wrong-endpoint rejection, process termination, and
terminal cache cleanup. It uses Linux `/proc` to verify that standalone command
and server processes exit.
Allow several minutes. On failure, it prints a temporary directory containing
logs and structured evidence. It does not require access to AAP or OpenShift:
the harness starts the HTTP test server in Python, outside the teaching playbook.
Use `--uri-only` for the changed URI example plus syntax/check-mode checks.

The content follows [Good Practices for Ansible](https://redhat-cop.github.io/automation-good-practices/):
descriptive names, prefixed inputs and internal state, role defaults and argument
validation, task-only orchestration, structured inventory, appropriate debug
verbosity, explicit change reporting, and documented execution limitations.
The command is a deliberate demonstration operation with no persistent business
changes, so it reports unchanged; temporary fixture and cache mutations report
changed. Repeated runs should have identical outcome sets. The CLI harness
removes its temporary fixture resources; presentation jobs leave the separately
managed HTTP service running. Collecting an already-cleaned job ID fails by design.

The strict production lint check applies without skips or suppressions. Review
these design properties separately; a lint pass alone cannot establish them.

The AAP EE's older ansible-core returns numeric `started`/`finished` values in
raw async results; newer CLI versions return booleans. The examples use the
`is finished` test and explicit boolean conversion where needed. In the tested
EE, debug summaries display return codes as strings, while raw command results
retain numeric `rc` values. Compare the actual value rather than relying on how
a particular Ansible version formats debug output.

## Cleanup and limitations

Positive polling normally removes completed job caches automatically, but it can
stop waiting before the async wrapper publishes its timeout. Separate polling
with `poll: 0` retains job caches even after explicit status collection. All async
lessons, including the role, leave retained caches to ephemeral EE teardown. For
CLI runs, inspect the job result after it finishes and remove a retained cache with
`ansible.builtin.async_status`, using its `jid` and `mode: cleanup` in the same
connection context and async directory. The CLI harness drains retained jobs and
removes their caches outside the teaching playbooks.

The standalone HTTP service remains available across jobs; remove it separately
with `oc delete -k demos/async-timeouts/service` when finished. The CLI harness
cleans up its own temporary HTTP process and files. Cleanup polling deliberately
accepts the command's failure result so the original teaching failure remains the
reported failure.

If role polling is exhausted before completion, the operation can continue until
its async limit. Never delete an active job's cache as a way of cancelling it.
The harness explicitly drains its exhaustion tests before removing their caches.

Cancelling an AAP job or killing a CLI process can bypass async cleanup. Commands
are bounded by their async limits; inspect retained job results
before removing leftovers. Temporary files may remain after interruption.

The HTTP service uses a small share of the existing OpenShift cluster's capacity;
no VM or persistent storage is provisioned. Remove its dedicated demo project
after presenting. In AAP,
remove the demo workflow, six job templates, and dedicated inventory/source when
finished. Remove a project or EE registration only if dedicated to this demo.

Keep one job slice, the default linear strategy, no `serial`, no privilege
escalation, and blank limits/tags for the presentation. Unreachable hosts and
invalid task definitions do not enter rescue. Launch failures can still fail a
job normally. The demo does not promise cancellation, recovery across disconnected
jobs, parallel artifact merging, or fleet-scale performance from three local aliases.
