# AAP configuration

Replace this checklist with the demo's tested AAP setup. Remove this directory
for a CLI-only demo.

## Project

- SCM URL: this repository's clone URL.
- SCM branch or tag: record the tested revision.
- Synchronize the project before creating job templates.

## Execution environment

Record the image registry location, tested tag or digest, and required registry
credentials. Link to custom build instructions when applicable.

## Inventory and credentials

Document required host groups, inventory source configuration, variables, and
credential types. The starter inventory uses localhost; in AAP this targets the
execution environment container.

## Job templates

| Setting | Value |
| --- | --- |
| Project | Project linked to this repository |
| Playbook | `demos/<demo-name>/playbooks/demo.yml` |
| Inventory | Record the configured inventory |
| Credentials | Record required credential types, or none |
| Execution environment | Record the tested image |
| Extra variables | Document values and defaults |
| Survey | Document fields and variable mappings, or none |
| Privilege escalation | Document whether required |

Document additional setup or cleanup templates if needed. Include workflow node
relationships and approval steps for workflow demonstrations.

## Launch and verify

Document which job or workflow to launch, required inputs, expected results, and
cleanup. Record the AAP version used for validation.

## Automated configuration

If provided, document the tooling, dependencies, credentials, commands, and
resources managed by files in `configuration/`. AAP does not automatically import
this directory.
