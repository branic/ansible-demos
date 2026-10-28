# Configure and validate the demo in AAP 2.7

Controller execution is **pending lab validation**. These are manual lab setup
instructions. Record actual results and the selected EE image digest before
claiming AAP support or aligning slides with controller output.

## Project, execution environment, and inventory

1. Create or reuse an SCM project pointing to this repository and the demo
   revision. Synchronize it before creating templates.
2. Choose an existing AAP 2.7-compatible EE containing Python 3 and ansible-core.
   No external collections, Python packages, or OS services are required.
3. Create inventory `demo_async_timeouts`. Add a **Sourced from a Project** source
   using this project and `demos/async-timeouts/inventory/demo.yml`. The adjacent
   `group_vars` and `host_vars` directories supply the scenario and local
   connection settings. Synchronize the source, importing variables.
4. Verify group `async_timeouts_demo` contains demo1, demo2, and demo3; inspect
   their imported delay and exit-code values. Check group settings include
   `ansible_connection: local` and the playbook Python interpreter expression.
5. Ensure execution nodes permit the EE's temporary loopback HTTP listener.
   There are no inbound external connections or published container ports.

Names use the `demo_` lab namespace; substitute your organization prefix when
adapting them. Reuse existing organization, project, and EE objects where useful.
The inventory aliases execute in the EE, not on the controller's host OS.

## Job templates

Use the synchronized project, `demo_async_timeouts` inventory, and the same EE
for all templates. Set job type **Run**, privilege escalation off, forks at least
3, one job slice, fact caching off, surveys off, and concurrent jobs off. Leave
Limit, job tags, and skip tags blank. No machine credential is needed; private
SCM or image registries may require their own credentials.

| Job template | Playbook relative to repository root | Extra variables |
| --- | --- | --- |
| `demo_demonstrate_uri_timeout` | `demos/async-timeouts/playbooks/demonstrate-uri-timeout.yml` | `{}` |
| `demo_demonstrate_positive_poll` | `demos/async-timeouts/playbooks/demonstrate-positive-poll.yml` | `{}` |
| `demo_demonstrate_separate_poll` | `demos/async-timeouts/playbooks/demonstrate-separate-poll.yml` | `{}` |
| `demo_collect_async_fail_host` | `demos/async-timeouts/playbooks/demonstrate-role.yml` | `async_timeouts_failure_policy: fail_host` |
| `demo_collect_async_exclude_hosts` | `demos/async-timeouts/playbooks/demonstrate-role.yml` | `async_timeouts_failure_policy: collect_and_exclude` |
| `demo_verify_async_survivors` | `demos/async-timeouts/playbooks/verify-survivors.yml` | `{}` |

Disable arbitrary launch-time prompts for the presentation. Default verbosity is
sufficient for the summaries; verbosity 1 adds the complete role result. The
native examples and fail-host template intentionally finish Failed.

## Workflow

Create `demo_workflow_async_collect_and_exclude` with no extra variables or
survey. Add `demo_collect_async_exclude_hosts` as the start node and connect it
to `demo_verify_async_survivors` with a **Success** link.

Do not define `__async_timeouts_failed_hosts` in inventory, job templates,
workflow variables, or surveys. It is a generated global `set_stats` artifact.
Artifact inheritance does not require arbitrary extra-variable prompts on the
child template. Use the same inventory and project revision for both nodes.

## Acceptance procedure

1. Run the URI template. Verify the one-second socket timeout is rescued, the
   six-second request succeeds, cleanup runs, and the job is Successful.
2. Run each native async template. Verify demo2 times out and demo3 exits 7, the
   job is Failed, and only demo1 reaches the continuation message. In the
   separate polling example, all hosts first reach `BEFORE COLLECTION`.
3. Launch `demo_collect_async_fail_host`. Verify all three outcomes and useful
   diagnostics. Only demo1 reaches `ROLE continued`; demo2 and demo3 have native
   failures; the job is Failed.
4. Launch the **complete workflow**. Verify the collection job is Successful.
   Its artifact contains `__async_timeouts_failed_hosts: [demo2, demo3]`, with
   order irrelevant. The unsuccessful hosts have `rescued=1`, `failed=0`, and
   `ignored=0`; only demo1 reaches the continuation message.
5. Verify the Success-linked child runs and prints `DOWNSTREAM verified demo1`,
   with no downstream action for demo2 or demo3. Both jobs and the workflow must
   be Successful. Initialization/exclusion tasks can still put excluded hosts
   in job recaps; inspect actual action messages.
6. Repeat the workflow to check fresh artifacts and absence of fixture conflicts.
7. In temporary copies of the templates/inventory, validate all-success and
   all-operation-error controls using delay 0 and exit codes 0 or 7. With every
   host recorded, the downstream job should exclude all hosts and still succeed.
   Restore or remove these copies before presenting.
8. Run each main example as job type **Check** in a temporary template copy.
   Verify no background command or HTTP fixture is launched. Restore type Run.

Record the completed lab validation here:

| Evidence | Value |
| --- | --- |
| AAP version | Pending; target 2.7 |
| Project revision | Pending |
| EE registry reference and digest | Pending |
| EE ansible-core / Python versions | Pending |
| URI / native example job IDs | Pending |
| Fail-host job ID and status | Pending |
| Collection workflow and child job IDs/statuses | Pending |
| Artifact and survivor verification | Pending |
| Repeat/control/check-mode results | Pending |
| Role run duration excluding queue/startup | Pending; target approximately 20–30 seconds |

## Troubleshooting and cleanup

- **Artifact missing or wrong:** check source synchronization, policy values,
  global `per_host: false` stats, and absence of manually defined output values.
- **Child does not run:** inspect the collection job's final status and the
  Success link. Unreachable hosts, failed launches, and cleanup errors can still
  cause unhandled failures.
- **Python or script missing:** confirm the repository revision and EE image.
  These scripts intentionally run locally from the checked-out project.
- **HTTP readiness fails:** inspect permissions for loopback listeners and
  temporary files. No external HTTP endpoint is needed.
- **Many retry messages:** a pending `until` condition produces retry messages;
  compare the final result and recap rather than treating each retry as a failure.
- **Healthy host waits:** the linear strategy synchronizes task progression.
- **Polling exhausted:** the operation can still be running. Inspect the async
  result in the same execution context before attempting cache cleanup.

Remove the workflow, six templates, and dedicated inventory/source after use.
Retain shared projects and EEs. See the [demo cleanup notes](../README.md#cleanup-and-limitations)
for interruption behavior and temporary resources.
