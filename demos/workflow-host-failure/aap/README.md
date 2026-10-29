# Configure the host failure workflow in AAP 2.6+

Configure the project, inventory, execution environment, job templates, and
workflow manually as described below.

## Project, inventory, and execution environment

1. Create or reuse an SCM project pointing to this repository and the demo branch.
   Synchronize it.
2. Create an inventory named **Host failure demo**. Add a source with **Sourced
   from a Project**, select the project and
   `demos/workflow-host-failure/inventory/demo.yml`, then synchronize it.
3. Verify `workflow_demo` contains `demo1`, `demo2`, and `demo3` with the source's
   local connection and Python interpreter variables.
4. Select an AAP 2.6-compatible EE with ansible-core 2.16+ for all three jobs.
   No extra collections are needed. Supply a registry credential if required.

## Job templates

Use these shared settings:

| Setting | Value |
| --- | --- |
| Job type | Run |
| Project | The synchronized repository project |
| Inventory | Host failure demo |
| Execution environment | The selected common EE |
| Credentials | None for the local inventory |
| Privilege escalation | Disabled |
| Limit, job tags, skip tags | Blank |
| Job slicing | 1 |
| Fact storage / caching | Disabled |
| Surveys | Disabled |
| Extra variables | `{}`; inputs belong on the workflow |

Create three templates with repository-relative playbook paths:

| Job template name | Playbook |
| --- | --- |
| Host failure - 1 - demonstrate | `demos/workflow-host-failure/playbooks/demo.yml` |
| Host failure - 2 - configure | `demos/workflow-host-failure/playbooks/configure.yml` |
| Host failure - 3 - verify | `demos/workflow-host-failure/playbooks/verify.yml` |

Do not define `__workflow_host_failure_failed_hosts` in inventory, templates, surveys, or
workflow extra variables: it is produced by the jobs. Artifact inheritance does
not require enabling arbitrary extra variable prompts on the child jobs.

## Workflow template

Create **Host failure - continue survivors** under **Automation Execution →
Templates**, with these extra variables:

```yaml
workflow_host_failure_initial_fail_hosts:
  - demo2
workflow_host_failure_configure_fail_hosts: []
```

Leave Limit blank. In the workflow visualizer, add the demonstrate job as the
start node and connect:

| Parent | Child | Link condition |
| --- | --- | --- |
| 1 - demonstrate | 2 - configure | Success |
| 2 - configure | 3 - verify | Success |

Save the workflow. The intentional failures are rescued, allowing these Success
links to run the following jobs. Unhandled failures stop this branch.

## Present and verify

1. Launch the complete workflow with defaults.
2. Show the simulated failure on `demo2` in stage 1, followed by its rescue tasks.
   Only `demo1` and `demo3` print `STAGE 1 continued`. The recap has `rescued=1`
   and `failed=0` for `demo2`; the job is **Successful**.
3. Inspect the job artifacts in job details or the job API response's `artifacts`
   field. Expect `__workflow_host_failure_failed_hosts: [demo2]`.
4. Stage 2 skips `demo2`. Only `demo1` and `demo3` print `STAGE 2 configured`.
   Its artifact still contains `__workflow_host_failure_failed_hosts: [demo2]`.
5. Stage 3 skips `demo2` and prints `STAGE 3 verified` for `demo1` and `demo3`.
   Failed hosts may appear in recaps due to skip handling or initialization;
   show the action messages to demonstrate which hosts actually did the work.
6. All three jobs and the workflow finish **Successful**.

Rerun with `workflow_host_failure_configure_fail_hosts: [demo3]`: stage 2 rescues `demo3`
and exports `__workflow_host_failure_failed_hosts: [demo2, demo3]`. Only `demo1` reaches the final
verification action. List order may vary.

Set `workflow_host_failure_initial_fail_hosts: [demo1, demo2, demo3]` to show every host rescued
and recorded. Later jobs skip all hosts and still succeed. For an all-success
control, set both failure inputs to `[]`; all three hosts finish each action.
Restore defaults for the next presentation.

## Troubleshooting and cleanup

- **Next job never starts:** check the parent job actually succeeded and the link
  is Success. Unreachable hosts and unprotected task failures are not rescued.
- **A failed host runs later actions:** inspect the parent's `__workflow_host_failure_failed_hosts`
  artifact, remove manually defined output variables, and check every job uses
  the same synchronized inventory and project branch.
- **Earlier failures disappear after stage 2:** ensure its initialization task
  republishes the inherited list before it appends new failures.
- **Local ping fails:** confirm the EE contains Python and ansible-core. All three
  local aliases execute inside the container.

See the [demo README](../README.md#cleanup) for cleanup and limitations. Downstream
templates launched alone default to an empty failed list; launch the workflow
to exercise the complete handoff.
