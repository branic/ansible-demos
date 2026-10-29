# Configure the demo in AAP 2.7

Configure six job templates and two workflows using a shared inventory, project,
and execution environment (EE).

## Project, execution environment, and inventory

1. Create or reuse an SCM project pointing to
   `https://github.com/branic/ansible-demos.git`. Select the branch or revision
   containing the demo and synchronize it before creating templates. The lab
   project name is `demo_async_timeouts_project`.
2. Choose an AAP-compatible EE with Ansible 2.16+ and use the same Ansible
   version for CLI execution. No additional collections are required.
3. Create inventory `demo_async_timeouts`. Add a **Sourced from a Project** source
   using this project and `demos/async-timeouts/inventory/demo.yml`. The adjacent
   `group_vars` and `host_vars` directories supply the scenario and local
   connection settings. Synchronize the source, importing variables.
4. Confirm group `async_timeouts_demo` contains demo1, demo2, and demo3, with
   their delay and exit-code values imported.
5. Confirm the EE can reach `https://httpbin.org/delay/3` for the URI example.

Substitute your organization's naming prefix for `demo_` as needed.

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

Disable launch-time prompts for the presentation. Default verbosity is
sufficient for failure details; verbosity 1 adds successful role results. The
native examples and fail-host template intentionally finish Failed.

## Workflows

Create `demo_workflow_async_collect_and_exclude` with no extra variables or
survey. Add `demo_collect_async_exclude_hosts` as the start node and connect it
to `demo_verify_async_survivors` with a **Success** link.

Copy that workflow as `demo_workflow_async_fail_host`, replacing only its start
node's job template with `demo_collect_async_fail_host`. Keep the same
Success-linked verification node and workflow settings, with no extra variables
or survey. With the default mixed inventory, the first job fails and the
verification node does not run.

| Workflow | Start job template | Default mixed outcome |
| --- | --- | --- |
| `demo_workflow_async_fail_host` | `demo_collect_async_fail_host` | Failed; verification does not run |
| `demo_workflow_async_collect_and_exclude` | `demo_collect_async_exclude_hosts` | Successful; verification runs only on demo1 |

Do not define `__async_timeouts_failed_hosts` in inventory, job templates,
workflow variables, or surveys. It is a generated global `set_stats` artifact.
Artifact inheritance does not require extra-variable prompts on the
child template. Use the same inventory and project revision for both nodes.

## Run the demo

1. Run the URI template. The first request should report a socket timeout, and
   the second should succeed.
2. Run the positive-poll and separate-poll templates. Both finish Failed;
   only demo1 reaches the continuation message. In the separate-poll example,
   all hosts first reach `BEFORE COLLECTION`.
3. Launch both workflows and compare their outcomes using the table above.
   The collection workflow exports demo2 and demo3 in
   `__async_timeouts_failed_hosts`; its child prints `DOWNSTREAM verified demo1`.

## Troubleshooting and cleanup

- **Artifact missing or wrong:** check source synchronization, policy values,
  global `per_host: false` stats, and absence of manually defined output values.
- **Child does not run:** inspect the collection job's final status and the
  Success link. Unreachable hosts and failed launches can still
  cause unhandled failures.
- **URI endpoint fails:** check HTTPS access to `httpbin.org` from the EE and
  confirm `async_timeouts_http_url` points to `/delay/3`.
- **Polling exhausted:** the operation can still be running. Inspect the async
  result in the same execution context before attempting cache cleanup.

Remove both workflows, six job templates, and dedicated inventory/source after use.
Retain shared projects and EEs. See the [demo cleanup notes](../README.md#cleanup-and-limitations)
for async cache handling.
