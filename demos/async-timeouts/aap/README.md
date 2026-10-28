# Configure and validate the demo in AAP 2.7

Controller and EE validation passed on **AAP 2.7.20261019**. The manual setup
instructions below reproduce the demo; the
[completed lab validation](#completed-lab-validation) records actual job results
and the selected image digest. Repeat acceptance checks when changing the code,
platform, or EE.

## Project, execution environment, and inventory

1. Create or reuse an SCM project pointing to
   `https://github.com/branic/ansible-demos.git` and the demo revision. The lab
   project is `demo_async_timeouts_project`, using branch
   `feature/async-timeouts-demo`. Synchronize it before creating templates.
2. Choose an existing AAP 2.7-compatible EE containing Python 3 and ansible-core.
   No external collections, Python packages, or OS services are required.
3. Create inventory `demo_async_timeouts`. Add a **Sourced from a Project** source
   using this project and `demos/async-timeouts/inventory/demo.yml`. The adjacent
   `group_vars` and `host_vars` directories supply the scenario and local
   connection settings. Synchronize the source, importing variables.
4. Verify group `async_timeouts_demo` contains demo1, demo2, and demo3; inspect
   their imported delay and exit-code values. Check group settings include
   `ansible_connection: local` and the playbook Python interpreter expression.
5. [Deploy the standalone HTTP service](../service/README.md#deploy) once before
   running the URI lesson. Its container runs in the `async-timeouts-demo`
   OpenShift project. Confirm AAP execution pods can resolve and reach its
   ClusterIP Service URL from the imported `async_timeouts_http_url` variable.
   An AAP instance outside that cluster can use the Route URL instead.

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
   six-second request succeeds, and the job is Successful. Repeat the job and
   confirm the separate service stays available; the job must not provision or
   tear down the HTTP container.
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
6. Repeat the workflow to check fresh artifacts and consistent survivor sets.
7. In temporary copies of the templates/inventory, validate all-success and
   all-operation-error controls using delay 0 and exit codes 0 or 7. With every
   host recorded, the downstream job should exclude all hosts and still succeed.
   Restore or remove these copies before presenting.
8. Run each main example as job type **Check** in a temporary template copy.
   Verify no background command or HTTP request is executed. Restore type Run.

## Completed lab validation

Validated on October 28, 2026, against
`https://basic-aap-aap-demo.apps-crc.testing`. All acceptance assertions checked
controller API job events and recaps, rather than treating a completed launch
or a workflow's top-level status alone as success. The complete sanitized
[validation evidence](validation.json) records each job's status, revision,
artifacts, host results, and timing. No credentials are included.

### Original full-matrix validation

These runs validated the initial implementation. Its URI job managed a temporary
server inside the playbook. The standalone service refactor and its new job IDs
are recorded separately below; the async role and native async examples retain
their original behavior.

| Evidence | Value |
| --- | --- |
| AAP version | 2.7.20261019; automation controller 4.8.12 |
| Tested code revision | `0c367892e5732ca7fbcb5813e7a5e653390cb3d9` on `feature/async-timeouts-demo` |
| EE registry reference and digest | `registry.redhat.io/ansible-automation-platform-27/ee-supported-rhel9@sha256:b08dcf736e08e75c4c6b462545bbce85690cc55c45fee3d0eb1516a28b149473` |
| EE ansible-core / Python / OS | 2.16.19 / 3.12.15 / RHEL 9.8 |
| URI / native example jobs | 7 Successful; 8 and 9 Failed as intended |
| Fail-host role job | 10 Failed as intended; only demo1 continued |
| Collection workflow | 11 Successful; collection job 12 and verification job 13 Successful |
| Repeat workflow | 14 Successful; collection job 15 and verification job 16 Successful |
| Artifact and survivor verification | Both mixed workflows exported demo2/demo3, inherited the actual artifact in the child, and ran downstream work only on demo1 |
| All-success control | Job 17 Successful; workflow 18 and jobs 19/20 Successful; empty artifact and all three hosts verified |
| All-unsuccessful control | Job 21 Failed as intended; workflow 22 and jobs 23/24 Successful; all three hosts recorded and none performed downstream work |
| Check-mode jobs | 25–30 Successful; no background commands, HTTP operations, cache operations, or stats publication executed |
| Mixed role job duration | 19.9–20.2 seconds of controller elapsed time |
| Complete mixed workflow duration | 23.9–24.1 seconds of controller elapsed time |

Controller elapsed time excludes queue time and includes some runner setup.
The async execution limit remains 10 seconds: wrapper enforcement and collection
overhead explain the longer observed job duration. The URI job took 9.7 seconds,
and native polling jobs took 19.7–19.9 seconds.

The mixed collection recaps had `rescued=1`, `failed=0`, and `ignored=0` on demo2
and demo3. The fail-host recap had `rescued=1` plus `failed=1` on each. Artifact
list order differed between repeats, as expected. Temporary control/check-mode
templates and the temporary control workflow were removed after validation;
the six presentation templates and main workflow remain available with their
original fixed policies and inventory scenarios.

Lab resource IDs are project **7**, inventory **2**, inventory source **8**, job
templates **9–14**, and workflow template **15**. These IDs belong to this lab,
not to a portable configuration. The code was tested directly from GitHub;
an initial temporary archive-source pod, Service, and ConfigMap were removed.

### Standalone HTTP service validation

The refactor was validated against code revision
`6166162af74848106e726354e19c18c2f7828cc0` on the same branch and AAP/EE versions.
The service was deployed with `oc apply -k demos/async-timeouts/service` on
OpenShift **4.22.14**, using Python **3.12.15** in the pinned public UBI image.
See [service setup and cleanup](../service/README.md) for the complete manifest
and container image reference.

| Evidence | Result |
| --- | --- |
| URI jobs | 38 and 39 Successful; 7.9–8.0 seconds each |
| URI recap | demo1: `ok=3`, `changed=0`, `rescued=1`, `failed=0`, `ignored=0` |
| Service access | AAP used the imported ClusterIP URL; CLI execution through the Route also passed |
| URI Check job | 40 Successful; no HTTP calls or server management tasks executed |
| Wrong-endpoint job | 41 Failed as intended when `/healthz` returned immediately |
| Workflow regression | 42 Successful; jobs 43/44 Successful; demo2/demo3 recorded, downstream action only on demo1 |
| Service lifecycle | Same pod stayed ready with zero restarts across the jobs; no setup/teardown tasks in the lesson |
| Manifest repeatability | Reapplying unchanged Kustomize files left all resources unchanged |
| Local verification | Updated URI integration checks, repeated runs, wrong-endpoint rejection, syntax, and check mode passed |

The HTTP container remains running in project `async-timeouts-demo` for the
presentation. Temporary Check and wrong-endpoint templates were removed. The
original AAP URI template remains type Run with no additional launch prompts.
The current URI playbook has no async launch, temporary-directory handling,
server startup, or teardown tasks. Its only endpoint input is
`async_timeouts_http_url`.

The URI lesson was subsequently simplified to two requests and a rescue that
displays the failure. Outcome assertions now live in the CLI harness; a fast
endpoint no longer makes the teaching job fail. The AAP evidence above records
the earlier version with assertions in the playbook. The simplified version has
not yet been revalidated in AAP.

Both native async lessons now leave retained job caches to ephemeral EE teardown.
The separate-poll lesson also shows the launch directly in the playbook. These
changes have passed CLI checks; AAP has not yet been revalidated.

## Troubleshooting and cleanup

- **Artifact missing or wrong:** check source synchronization, policy values,
  global `per_host: false` stats, and absence of manually defined output values.
- **Child does not run:** inspect the collection job's final status and the
  Success link. Unreachable hosts, failed launches, and cleanup errors can still
  cause unhandled failures.
- **Python or script missing:** confirm the repository revision and EE image.
  These scripts intentionally run locally from the checked-out project.
- **URI endpoint fails:** confirm the standalone Deployment is ready and the
  imported `async_timeouts_http_url` points to `/slow`. Check cluster DNS and
  network policy between the AAP and service projects. Use the Route URL if
  execution runs outside this cluster.
- **Many retry messages:** a pending `until` condition produces retry messages;
  compare the final result and recap rather than treating each retry as a failure.
- **Healthy host waits:** the linear strategy synchronizes task progression.
- **Polling exhausted:** the operation can still be running. Inspect the async
  result in the same execution context before attempting cache cleanup.

Remove the workflow, six templates, and dedicated inventory/source after use.
Remove the standalone HTTP service with `oc delete -k demos/async-timeouts/service`.
Retain shared projects and EEs. See the [demo cleanup notes](../README.md#cleanup-and-limitations)
for interruption behavior and temporary resources.
