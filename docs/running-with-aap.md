# Running with AAP

Use the AAP version and execution environment documented by the selected demo.
This guide describes automation controller job execution; demos involving other
AAP components must document their additional setup.

## Configure the project

Create a source-controlled project pointing to this repository and the desired
branch or tag, then synchronize it. The repository root is the project root.

Select playbooks using their full repository-relative paths, for example
`demos/<demo-name>/playbooks/demo.yml`. Do not rely on changing the project root
to a demo subdirectory or on a nested `ansible.cfg` being selected automatically.

## Configure the runtime and inventory

1. Register the execution environment image documented by the demo. Configure
   registry credentials if the image requires them.
2. Create or select an inventory with the host groups expected by the playbooks.
   Use the demo's example inventory as guidance. If using an SCM inventory source,
   document and select a committed inventory file suitable for your environment.
3. Create the required machine, cloud, vault, or other credentials and attach them
   where the demo specifies.

`localhost` in an AAP playbook refers to the execution environment container.
Local CLI files, installed packages, and credentials are not automatically
available there.

## Configure and launch templates

Follow the demo's `aap/README.md` to configure:

- Project and repository-relative playbook path.
- Inventory and credential types.
- Execution environment image and tested version or digest.
- Extra variables, surveys, limits, tags, and privilege escalation settings.
- Workflow nodes, dependencies, and approval steps when applicable.

Launch the documented job or workflow, verify the outcome, and run cleanup.
Use AAP credentials for secrets rather than committing them or putting them in
ordinary survey answers or example variables.

## Dependency discovery

Automation controller can install project dependencies from root-level
`collections/requirements.yml` and `roles/requirements.yml`. The per-demo files
in this repository are not automatically discovered at those locations.

Use each demo's execution environment to provide its dependencies. If a shared
project-level requirements file is added later, manage its versions deliberately
because it applies across demos and can override collections in the image.

See [Red Hat's project documentation](https://docs.redhat.com/en/documentation/red_hat_ansible_automation_platform/2.5/html/using_automation_execution/controller-projects)
and [Execution environments](execution-environments.md).
