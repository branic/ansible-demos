# Demo title

> Starter template: replace the placeholders and tasks before publishing.

Describe what this demo teaches and its expected outcome.

## Supported execution modes

Choose **CLI**, **AAP**, or **Both** after validating the relevant modes.
This starter has not been validated as a published demo.

## Prerequisites and tested versions

Record required infrastructure, permissions, network access, and credentials.

| Component | Tested version or requirement |
| --- | --- |
| Ansible / ansible-core | To be recorded |
| AAP, if applicable | To be recorded |
| Collections | See `collections/requirements.yml`; pin tested versions |
| Target platforms | To be recorded |
| Execution environment | Record image tag or digest, if applicable |

## Inputs

| Variable | Purpose | Default | Secret? |
| --- | --- | --- | --- |
| `demo_message` | Starter message; replace with actual demo inputs | `Demo starter` | No |

Use `vars/demo.yml.example` for non-secret example inputs. Document credential
sources separately.

## Setup

Describe lab provisioning, dependencies, inventory groups, and configuration.
Document whether setup creates resources that incur costs.

## Run with the CLI

Replace `<demo-name>` with this demo's directory name. Run from the repository
root after preparing Ansible and the dependencies:

```bash
ansible-galaxy collection install -r demos/<demo-name>/collections/requirements.yml
cp demos/<demo-name>/inventory/hosts.yml.example demos/<demo-name>/inventory/hosts.yml
cp demos/<demo-name>/vars/demo.yml.example demos/<demo-name>/vars/demo.yml
ansible-playbook -i demos/<demo-name>/inventory/hosts.yml \
  demos/<demo-name>/playbooks/demo.yml \
  -e @demos/<demo-name>/vars/demo.yml
```

Remove the collection installation command if no collections are required. Edit
the inventory and variable copies for your lab before running actual automation.
The starter inventory targets localhost, and the starter playbook only prints a
message.

Remove this section for an AAP-only demo.

## Run with AAP

Follow [AAP configuration](aap/README.md). Record the exact template or workflow
to launch and any required launch-time inputs. Remove this section and the `aap/`
directory for a CLI-only demo.

## Verify

Before publishing, install the repository lint tooling and this demo's
dependencies, then run from the repository root:

```bash
ansible-lint --offline --config-file .ansible-lint demos/<demo-name>
```

The production profile must pass without warnings. See
[contribution guidelines](../../CONTRIBUTING.md) for setup and CI requirements.

Describe observable success criteria, expected output, and how to inspect target
resources. The starter playbook only prints `demo_message`.

## Cleanup

Document resource removal and how to verify it. Replace the starter cleanup
playbook with actual cleanup when the demo creates resources. State explicitly
when a demo requires no cleanup.

## Troubleshooting and limitations

Record common failures, environment assumptions, and unsupported scenarios.
